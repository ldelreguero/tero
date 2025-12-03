import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import List, cast, Any, AsyncIterator, Tuple, Optional, Dict

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import LLMResult
from langchain_core.prompts import ChatPromptTemplate
from openevals.llm import create_async_llm_as_judge
from openevals.types import EvaluatorResult
from sqlmodel.ext.asyncio.session import AsyncSession
from sse_starlette.event import ServerSentEvent

from ...agents.evaluators.domain import Evaluator
from ...agents.evaluators.repos import EvaluatorRepository
from ...ai_models import ai_factory
from ...ai_models.repos import AiModelRepository
from ...ai_models.domain import LlmModel, LlmModelType, LlmTemperature, ReasoningEffort
from ...core.env import env
from ...core.repos import engine
from ...threads.domain import ThreadMessage, Thread, ThreadMessageOrigin, AgentMessageEvent, AgentActionEvent
from ...threads.repos import ThreadMessageRepository, ThreadRepository
from ...threads.engine import AgentEngine
from ...usage.domain import MessageUsage
from ...usage.repos import UsageRepository
from ..domain import Agent
from .domain import TestCase, TestCaseResultStatus, TestCaseEventType, TestCaseResult, TestSuiteRun, TestSuiteEventType, TestSuiteRunStatus
from .repos import TestCaseResultRepository, TestSuiteRunRepository


logger = logging.getLogger(__name__)
EVALUATOR_HUMAN_MESSAGE = """
Compare the actual output with the reference output based on these criteria:
1. Semantic equivalence - Does the actual output convey the same meaning as the reference output?
2. Completeness - Does the actual output contain all key information from the reference output?
3. Accuracy - Is the actual output factually correct when compared to the reference output?
4. Relevance - Does the actual output appropriately address the input?
5. Conciseness - Does the actual output avoid including extra information not present in the reference output? If the reference output is concise the response should also be concise for example if the reference output is "Agent response" the actual output should also be "Agent response" or similar.

Be lenient with minor differences in wording, formatting, or style. Focus on whether the core meaning and key information match. Be strict about factual errors, missing critical information, or extraneous details that go beyond the expected output.

Respond with 'Y' if the actual output sufficiently matches the reference output, or 'N' if there are significant discrepancies. Then provide a brief explanation.


Input:
{{inputs}}

Reference Output:
{{reference_outputs}}

Actual Output:
{{outputs}}
"""
EVALUATOR_DEFAULT_TEMPERATURE = LlmTemperature.NEUTRAL
EVALUATOR_DEFAULT_REASONING_EFFORT = ReasoningEffort.MEDIUM


class EvaluatorUsageTrackingCallback(AsyncCallbackHandler):
    def __init__(self, usage: MessageUsage, model: LlmModel):
        self.usage = usage
        self.model = model

    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
         # Try to extract usage from llm_output first (most common format)
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage')
            if token_usage:
                self.usage.increment_with_metadata(UsageMetadata(
                    input_tokens=token_usage.get('prompt_tokens', 0),
                    output_tokens=token_usage.get('completion_tokens', 0),
                    total_tokens=token_usage.get('total_tokens', 0)
                ), self.model)
                return
        
        # Fallback: try to extract from generation_info
        if response.generations:
            for generation_list in response.generations:
                for generation in generation_list:
                    if hasattr(generation, 'generation_info') and generation.generation_info:
                        token_usage = generation.generation_info.get('token_usage')
                        if token_usage:
                            self.usage.increment_with_metadata(UsageMetadata(
                                input_tokens=token_usage.get('prompt_tokens', 0),
                                output_tokens=token_usage.get('completion_tokens', 0),
                                total_tokens=token_usage.get('total_tokens', 0)
                            ), self.model)
                            return


class TestCaseRunner:

    def __init__(self, db: AsyncSession):
        self._db = db
    
    def _build_test_case_evaluator_prompt(self, evaluator: Optional[Evaluator]) -> ChatPromptTemplate:
        human_message = evaluator.prompt if evaluator else EVALUATOR_HUMAN_MESSAGE
        return ChatPromptTemplate(
            [("system", "You are an expert evaluator assessing whether the actual output from an AI agent matches the expected output for a given test case."),
                ("human", human_message)],
            template_format="mustache"
        )

    async def run_test_case_stream(self, test_case: TestCase, agent: Agent, user_id: int, result: TestCaseResult, stop_event: asyncio.Event) -> AsyncIterator[Tuple[TestCaseEventType, Any]]:
        results_repo = TestCaseResultRepository(self._db)
        try:
            messages = await ThreadMessageRepository(self._db).find_by_thread_id(test_case.thread_id)

            if not messages:
                result.status = TestCaseResultStatus.SKIPPED
                result = await results_repo.save(result)

                yield (TestCaseEventType.METADATA, {
                    "testCaseId": test_case.thread_id,
                    "resultId": result.id,
                })

                yield (TestCaseEventType.PHASE, {
                    "phase": "completed",
                    "status": TestCaseResultStatus.SKIPPED.value,
                    "evaluation": None
                })
                return

            execution_thread = await ThreadRepository(self._db).add(Thread(
                agent_id=agent.id,
                user_id=user_id,
                is_test_case=True
            ))

            result.thread_id = execution_thread.id
            result.status = TestCaseResultStatus.RUNNING
            result = await results_repo.save(result)

            yield (TestCaseEventType.METADATA, {
                "testCaseId": test_case.thread_id,
                "resultId": result.id,
            })

            user_input = messages[0].text
            expected_output = messages[1].text if len(messages) > 1 else ""

            yield (TestCaseEventType.PHASE, {"phase": "executing"})

            actual_output = ""

            async for event_type, content in self._execute_agent_with_input_stream(agent, user_input, user_id, execution_thread.id, stop_event):
                if event_type == TestCaseEventType.AGENT_MESSAGE_COMPLETE:
                    actual_output += content["text"]
                    yield (event_type, content)
                elif event_type in [TestCaseEventType.USER_MESSAGE, TestCaseEventType.AGENT_MESSAGE_START,
                                    TestCaseEventType.AGENT_MESSAGE_CHUNK, TestCaseEventType.EXECUTION_STATUS]:
                    yield (event_type, content)

            if stop_event.is_set():
                result.status = TestCaseResultStatus.SKIPPED
                result.evaluator_analysis = None
                await results_repo.save(result)
                yield (TestCaseEventType.PHASE, {
                    "phase": "completed",
                    "status": TestCaseResultStatus.SKIPPED.value,
                    "evaluation": None
                })
                return

            yield (TestCaseEventType.PHASE, {"phase": "evaluating"})

            evaluation_result = await self._evaluate_test_case_result(
                user_input, expected_output, actual_output, user_id, agent, test_case
            )
            evaluation_result_status = cast(bool, evaluation_result.get("score"))
            evaluation_result_analysis = (evaluation_result.get("comment") or "").replace("Thus, the score should be: SCORE_YOU_ASSIGN.", "")
            final_status = TestCaseResultStatus.SUCCESS if evaluation_result_status else TestCaseResultStatus.FAILURE
            result.status = final_status
            result.evaluator_analysis = evaluation_result_analysis
            await results_repo.save(result)

            yield (TestCaseEventType.PHASE, {
                "phase": "completed",
                "status": final_status.value,
                "evaluation": {
                    "passed": evaluation_result_status,
                }
            })

        except Exception:
            logger.exception(f"Unexpected error running test case {test_case.thread_id}")
            try:
                result.status = TestCaseResultStatus.ERROR
                await results_repo.save(result)
            except Exception:
                pass
            yield (TestCaseEventType.PHASE, {
                "phase": "completed",
                "status": TestCaseResultStatus.ERROR.value,
                "evaluation": None
            })
    
    async def _execute_agent_with_input_stream(self, agent: Agent, user_input: str, user_id: int, thread_id: int, stop_event: asyncio.Event) -> AsyncIterator[Tuple[TestCaseEventType, Any]]:
        thread_message_repo = ThreadMessageRepository(self._db)
        input_message = await thread_message_repo.add(ThreadMessage(
            text=user_input,
            origin=ThreadMessageOrigin.USER,
            timestamp=datetime.now(timezone.utc),
            thread_id=thread_id
        ))
        
        yield (TestCaseEventType.USER_MESSAGE, {
            "id": input_message.id,
            "text": input_message.text,
        })
        
        input_message_usage = MessageUsage(user_id=user_id, agent_id=agent.id, model_id=agent.model_id, message_id=input_message.id)
        engine = AgentEngine(agent, user_id, self._db)
        
        response_message = await thread_message_repo.add(ThreadMessage(
            text="", 
            origin=ThreadMessageOrigin.AGENT,
            timestamp=datetime.now(timezone.utc),
            thread_id=thread_id,
            parent_id=input_message.id
        ))

        yield (TestCaseEventType.AGENT_MESSAGE_START, {
            "id": response_message.id
        })
        
        complete_response = ""
        status_updates: List[AgentActionEvent] = []

        async for event in engine.answer([input_message], input_message_usage, stop_event):
            if isinstance(event, AgentActionEvent):
                status_updates.append(event)
                yield (TestCaseEventType.EXECUTION_STATUS, event)
            elif isinstance(event, AgentMessageEvent):
                complete_response += event.content
                yield (TestCaseEventType.AGENT_MESSAGE_CHUNK, {
                    "id": response_message.id,
                    "chunk": event.content
                })
        
        response_message.text = complete_response
        response_message.timestamp = datetime.now(timezone.utc)
        response_message.status_updates = [event.model_dump(mode="json", by_alias=True) for event in status_updates] if status_updates else None
        await thread_message_repo.update(response_message)
        await UsageRepository(self._db).add(input_message_usage)

        yield (TestCaseEventType.AGENT_MESSAGE_COMPLETE, {
            "id": response_message.id,
            "text": complete_response,
        })

    async def _find_evaluator(self, agent: Agent, test_case: TestCase) -> Optional[Evaluator]:
        evaluator_repo = EvaluatorRepository(self._db)
        test_case_evaluator = await evaluator_repo.find_by_id(test_case.evaluator_id) if test_case.evaluator_id else None
        return test_case_evaluator if test_case_evaluator else await evaluator_repo.find_by_id(agent.evaluator_id) if agent.evaluator_id else None

    def _get_evaluator_temperature(self, llm_model: LlmModel, evaluator: Optional[Evaluator]) -> Optional[float]:
        temperature = evaluator.temperature.get_float() if evaluator else EVALUATOR_DEFAULT_TEMPERATURE.get_float()
        return temperature if llm_model.model_type == LlmModelType.CHAT else None
    
    def _get_evaluator_reasoning_effort(self, llm_model: LlmModel, evaluator: Optional[Evaluator]) -> Optional[str]:
        reasoning_effort = evaluator.reasoning_effort.value.lower() if evaluator else EVALUATOR_DEFAULT_REASONING_EFFORT.value.lower()
        return reasoning_effort if llm_model.model_type == LlmModelType.REASONING else None
    
    async def _evaluate_test_case_result(
        self, 
        user_input: str, 
        expected_output: str, 
        actual_output: str,
        user_id: int,
        agent: Agent,
        test_case: TestCase
    ) -> EvaluatorResult:
        llm_model_repo = AiModelRepository(self._db)
        evaluator = await self._find_evaluator(agent, test_case)
        evaluator_model = cast(LlmModel, await llm_model_repo.find_by_id(evaluator.model_id if evaluator else cast(str, env.internal_evaluator_model)))
        evaluator_usage = MessageUsage(user_id=user_id, agent_id=agent.id, model_id=evaluator_model.id, message_id=None)
        usage_callback = EvaluatorUsageTrackingCallback(evaluator_usage, evaluator_model)

        judge_llm = ai_factory.build_chat_model(
            evaluator_model.id,
            temperature=self._get_evaluator_temperature(evaluator_model, evaluator),
            reasoning_effort=self._get_evaluator_reasoning_effort(evaluator_model, evaluator)
        )
        judge_llm.callbacks.append(usage_callback)
        judge = create_async_llm_as_judge(
            prompt=self._build_test_case_evaluator_prompt(evaluator),
            judge=judge_llm,
        )

        evaluation_result = await judge(
            inputs=user_input,
            outputs=actual_output,
            reference_outputs=expected_output
        )

        await UsageRepository(self._db).add(evaluator_usage)
        return cast(EvaluatorResult, evaluation_result)

    async def run_test_suite_stream(
        self,
        agent: Agent,
        all_test_cases: List[TestCase],
        test_cases_to_run: List[TestCase],
        user_id: int,
        suite_run: TestSuiteRun,
        stop_event: asyncio.Event
    ) -> AsyncIterator[bytes]:
        suite_repo = TestSuiteRunRepository(self._db)
        results_repo = TestCaseResultRepository(self._db)

        try:
            test_case_ids_to_run = {tc.thread_id for tc in test_cases_to_run}

            pending_results: dict[int, TestCaseResult] = {}
            for test_case in all_test_cases:
                test_case_name = test_case.thread.name if test_case.thread else None
                if test_case.thread_id in test_case_ids_to_run:
                    pending_result = await results_repo.save(TestCaseResult(
                        test_case_id=test_case.thread_id,
                        test_suite_run_id=suite_run.id,
                        status=TestCaseResultStatus.PENDING,
                        test_case_name=test_case_name
                    ))
                    pending_results[test_case.thread_id] = pending_result
                else:
                    await results_repo.save(TestCaseResult(
                        test_case_id=test_case.thread_id,
                        test_suite_run_id=suite_run.id,
                        status=TestCaseResultStatus.SKIPPED,
                        test_case_name=test_case_name
                    ))

            yield ServerSentEvent(event=TestSuiteEventType.START.value, data=json.dumps({
                "suiteRunId": suite_run.id
            })).encode()

            passed = 0
            failed = 0
            errors = 0
            skipped = len(all_test_cases) - len(test_cases_to_run)

            for index, test_case in enumerate(test_cases_to_run):
                if stop_event.is_set():
                    async for skipped_event, counts_as_skip in self._skip_remaining_tests(
                        test_cases_to_run[index:],
                        pending_results,
                        results_repo
                    ):
                        if counts_as_skip:
                            skipped += 1
                        yield skipped_event
                    break

                result = pending_results[test_case.thread_id]
                yield ServerSentEvent(event=TestSuiteEventType.TEST_START.value, data=json.dumps({
                    "testCaseId": test_case.thread_id,
                    "resultId": result.id
                })).encode()

                async for event_type, content in self.run_test_case_stream(
                    test_case, agent, user_id, pending_results[test_case.thread_id], stop_event
                ):
                    if event_type == TestCaseEventType.PHASE and content.get("phase") == "completed":
                        status_value = content.get("status")
                        if status_value == TestCaseResultStatus.SUCCESS.value:
                            passed += 1
                        elif status_value == TestCaseResultStatus.FAILURE.value:
                            failed += 1
                        elif status_value == TestCaseResultStatus.SKIPPED.value:
                            skipped += 1
                        elif status_value == TestCaseResultStatus.ERROR.value:
                            errors += 1
                        else:
                            skipped += 1

                    yield ServerSentEvent(event=f"suite.test.{event_type.value}", data=json.dumps(content.model_dump() if event_type == TestCaseEventType.EXECUTION_STATUS else content)).encode()

                yield ServerSentEvent(event=TestSuiteEventType.TEST_COMPLETE.value, data=json.dumps({
                    "testCaseId": test_case.thread_id,
                    "resultId": result.id,
                    "status": result.status.value,
                    "evaluation": {
                        "analysis": result.evaluator_analysis
                    }
                })).encode()

            suite_run.completed_at = datetime.now(timezone.utc)
            suite_run.total_tests = len(all_test_cases)
            suite_run.passed_tests = passed
            suite_run.failed_tests = failed
            suite_run.error_tests = errors
            suite_run.skipped_tests = skipped
            suite_run.status = TestSuiteRunStatus.FAILURE if errors > 0 or failed > 0 or stop_event.is_set() else TestSuiteRunStatus.SUCCESS

            suite_run = await suite_repo.save(suite_run)

            yield ServerSentEvent(event=TestSuiteEventType.COMPLETE.value, data=json.dumps({
                "suiteRunId": suite_run.id,
                "status": suite_run.status.value,
                "totalTests": suite_run.total_tests,
                "passed": suite_run.passed_tests,
                "failed": suite_run.failed_tests,
                "errors": suite_run.error_tests,
                "skipped": suite_run.skipped_tests
            })).encode()

        except Exception:
            logger.exception(f"Error streaming test suite for agent {agent.id}")
            await cleanup_orphaned_suite_run(suite_run.id, agent.id)
            suite_run.status = TestSuiteRunStatus.FAILURE
            suite_run.completed_at = datetime.now(timezone.utc)
            suite_run = await suite_repo.save(suite_run)
            yield ServerSentEvent(event=TestSuiteEventType.ERROR.value, data=json.dumps({})).encode()

    async def _skip_remaining_tests(
        self,
        remaining_tests: List[TestCase],
        pending_results: Dict[int, TestCaseResult],
        results_repo: TestCaseResultRepository
    ) -> AsyncIterator[Tuple[bytes, bool]]:
        for test_case in remaining_tests:
            result = pending_results.get(test_case.thread_id)
            if not result:
                continue
            result.status = TestCaseResultStatus.SKIPPED
            result.evaluator_analysis = None
            await results_repo.save(result)
            test_complete_event = json.dumps({
                "testCaseId": test_case.thread_id,
                "resultId": result.id,
                "status": result.status.value,
                "evaluation": {
                    "analysis": result.evaluator_analysis
                }
            })
            phase_event = ServerSentEvent(event=f"suite.test.{TestCaseEventType.PHASE.value}", data=json.dumps({
                "phase": "completed",
                "status": result.status.value,
                "evaluation": None
            })).encode()
            yield (phase_event, True)
            yield (ServerSentEvent(event=TestSuiteEventType.TEST_COMPLETE.value, data=test_complete_event).encode(), False)


# Cleanup running or pending results for a suite in case of suite error or connection closed
# Has its own db session to be able to run on a background task
async def cleanup_orphaned_suite_run(suite_run_id: int, agent_id: int):
    async with AsyncSession(engine, expire_on_commit=False) as db:
        try:
            results_repo = TestCaseResultRepository(db)
            suite_repo = TestSuiteRunRepository(db)
            
            current_suite = await suite_repo.find_by_id_and_agent_id(suite_run_id, agent_id)
            if not current_suite or current_suite.status != TestSuiteRunStatus.RUNNING:
                return
            
            all_results = await results_repo.find_by_suite_run_id(suite_run_id)
            for result in all_results:
                if result.status in [TestCaseResultStatus.PENDING, TestCaseResultStatus.RUNNING]:
                    result.status = TestCaseResultStatus.SKIPPED
                    db.add(result)
            
            current_suite.status = TestSuiteRunStatus.FAILURE
            current_suite.completed_at = datetime.now(timezone.utc)
            
            current_suite.error_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.ERROR)
            current_suite.passed_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.SUCCESS)
            current_suite.failed_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.FAILURE)
            current_suite.skipped_tests = sum(1 for r in all_results if r.status == TestCaseResultStatus.SKIPPED)
            
            db.add(current_suite)
            
            await db.commit()
            
        except Exception as error:
            logger.exception(f"Error during background cleanup for suite {suite_run_id}: {error}")
            try:
                await db.rollback()
            except:
                pass
