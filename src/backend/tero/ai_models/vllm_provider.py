import io
import logging
import json
from typing import Any, Callable, Optional, Sequence, cast

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import AsyncOpenAI
from pydantic import SecretStr
from tokenizers import Tokenizer

from ..core.env import env
from .domain import AiModelProvider

logger = logging.getLogger(__name__)


class VllmAiProvider(AiModelProvider):

    def _build_chat_model(self, model: str, temperature: Optional[float], reasoning_effort: Optional[str], streaming: bool) -> BaseChatModel:
        vllm_model_id = env.vllm_model_id_mapping[model]
        return VLLMChatModel(
            base_url=env.vllm_base_url,
            api_key=env.vllm_api_key,
            model=vllm_model_id,
            temperature=temperature,
            streaming=streaming)

    def supports_model(self, model: str) -> bool:
        return model in env.vllm_model_id_mapping

    async def transcribe_audio(self, file: io.BytesIO, model: str) -> str:
        client = AsyncOpenAI(api_key=cast(SecretStr, env.vllm_api_key).get_secret_value())
        response = await client.audio.transcriptions.create(
            file=file,
            model=env.vllm_model_id_mapping[model]
        )
        return response.text

    def build_embedding(self, model: str) -> Embeddings:
        return OpenAIEmbeddings(
            api_key=env.vllm_api_key,
            model=env.vllm_model_id_mapping[model])

# this cache is used to avoid downloading the tokenizer for the same model multiple times
_hf_tokenizer_cache: dict[str, "HuggingFaceTokenizerEncoding"] = {}

class HuggingFaceTokenizerEncoding:
    def __init__(self, tokenizer, model_name: str):
        self._tokenizer = tokenizer
        self._model_name = model_name
    
    def encode(self, text: str, *, allowed_special: set = set(), disallowed_special: set = set()) -> list[int]:
        return self._tokenizer.encode(text).ids
    
    def decode(self, tokens: list[int], errors: str = "replace") -> str:
        return self._tokenizer.decode(tokens)
    
    def encode_ordinary(self, text: str) -> list[int]:
        return self._tokenizer.encode(text).ids
    
    @classmethod
    def from_pretrained(cls, model_name: str) -> Optional["HuggingFaceTokenizerEncoding"]:
        if model_name in _hf_tokenizer_cache:
            return _hf_tokenizer_cache[model_name]
        
        try:
            tokenizer = Tokenizer.from_pretrained(model_name)
            wrapper = cls(tokenizer, model_name)
            _hf_tokenizer_cache[model_name] = wrapper
            return wrapper
        except Exception as e:
            logger.debug(f"Failed to load HuggingFace tokenizer for {model_name}: {e}")
            return None

class VLLMChatModel(ChatOpenAI):
    _hf_tokenizer: Optional[HuggingFaceTokenizerEncoding] = None

    def _get_tokenizer(self) -> HuggingFaceTokenizerEncoding:
        if self._hf_tokenizer is None:
            self._hf_tokenizer = HuggingFaceTokenizerEncoding.from_pretrained(self.model_name)
        
        if self._hf_tokenizer is None:
            raise ValueError(
                f"Failed to load HuggingFace tokenizer for model '{self.model_name}'. "
                f"Verify the model exists on HuggingFace Hub and has a tokenizer available."
            )
        
        return self._hf_tokenizer

    def _get_encoding_model(self) -> tuple[str, HuggingFaceTokenizerEncoding]:  # type: ignore[override]
        return self.model_name, self._get_tokenizer()

    def get_num_tokens(self, text: str) -> int:
        tokenizer = self._get_tokenizer()
        return len(tokenizer.encode(text))

    def get_num_tokens_from_messages(
        self,
        messages: Sequence[BaseMessage],
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool] | None = None,
    ) -> int:
        tokenizer = self._get_tokenizer()
        total = 0
        for msg in messages:
            # Message overhead (role, separators, etc.)
            total += 4
            
            content = msg.content
            if isinstance(content, str):
                total += len(tokenizer.encode(content))
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        total += len(tokenizer.encode(item['text']))
                    elif isinstance(item, str):
                        total += len(tokenizer.encode(item))
        
        if tools:
            openai_tools = [convert_to_openai_tool(tool) for tool in tools]
            tools_json = json.dumps(openai_tools)
            total += len(tokenizer.encode(tools_json))
        
        total += 2
        return total
