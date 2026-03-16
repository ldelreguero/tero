from typing import Callable, List, Optional, Type

from langchain_core.messages import BaseMessage
from langchain_core.messages.utils import _default_text_splitter, _first_max_tokens

from ..ai_models.domain import LlmModel


def trim_messages_to_fit_model(
    messages: List[BaseMessage],
    token_counter: Callable[[List[BaseMessage]], int],
    model: LlmModel,
    reserved_tokens: int = 0,
    end_on: Optional[Type[BaseMessage]] = None,
) -> List[BaseMessage]:
    # we multiply by 0.9997 because we have identified that for gpt-5 which has 272k tokens limit, 
    # this calculation misseses in some cases 72 tokens (0.026% of the limit).
    # Since OpenAI token calculation logic is closed and we didn't find any way to actually get a better approximation, 
    # for the time being we use this value as approximation error threshold.
    max_tokens = max(
        0,
        int(model.token_limit * 0.9997)
        - reserved_tokens
        - model.output_token_limit,
    )
    return _first_max_tokens(
        messages,
        max_tokens=max_tokens,
        token_counter=token_counter,
        text_splitter=_default_text_splitter,
        partial_strategy="first",
        end_on=end_on,
    )
