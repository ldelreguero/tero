import io
from typing import Callable, Iterable, Optional, cast

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import AsyncOpenAI
from pydantic import SecretStr
import tiktoken

from ..core.env import env
from .domain import AiModelProvider


class OpenAIProvider(AiModelProvider):

    def _build_chat_model(self, model: str, temperature: Optional[float], reasoning_effort: Optional[str], streaming: bool) -> BaseChatModel:
        openai_model_id = env.openai_model_id_mapping[model]
        return ReasoningTokenCountingChatOpenAI(
            api_key=env.openai_api_key,
            model=openai_model_id,
            temperature=temperature,
            streaming=streaming)

    def supports_model(self, model: str) -> bool:
        return model in env.openai_model_id_mapping

    async def transcribe_audio(self, file: io.BytesIO, model: str) -> str:
        client = AsyncOpenAI(api_key=cast(SecretStr, env.openai_api_key).get_secret_value())
        response = await client.audio.transcriptions.create(
            file=file,
            model=env.openai_model_id_mapping[model]
        )
        return response.text

    def build_embedding(self, model: str, usage_tracker: Callable[[int], None]) -> Embeddings:
        return UsageTrackingOpenAIEmbeddings(
            usage_tracker=usage_tracker,
            api_key=env.openai_api_key,
            embedding_ctx_length=env.embedding_context_limit,
            model=env.openai_model_id_mapping[model])

    def count_tokens(self, txt: str, model: str) -> int:
        return count_tokens(txt, model)


def count_tokens(txt: str, model: str) -> int:
    return len(tiktoken.encoding_for_model(model).encode(txt))


class ReasoningTokenCountingChatOpenAI(ChatOpenAI):

    # we override this method which is the one used by get_num_tokens_from_messages to count the tokens
    def _get_encoding_model(self) -> tuple[str, tiktoken.Encoding]:
        return get_encoding_model(self.model_name, lambda: ChatOpenAI._get_encoding_model(self))


def get_encoding_model(model_name: Optional[str], default: Callable[[], tuple[str, tiktoken.Encoding]]) -> tuple[str, tiktoken.Encoding]:
        if model_name and model_name.startswith("o"):
            # we return gpt-4o for o- series since it is supported by existing implementation of get_num_tokens_from_messages
            return "gpt-4o", tiktoken.get_encoding("o200k_base")
        return default()


class UsageTrackingOpenAIEmbeddings(OpenAIEmbeddings):
    usage_tracker: Callable[[int], None]

    def _tokenize(self, texts: list[str], chunk_size: int) -> tuple[Iterable[int], list[list[int] | str], list[int], list[int]]:
        ret = super()._tokenize(texts, chunk_size)
        self.usage_tracker(sum(ret[3]))
        return ret
