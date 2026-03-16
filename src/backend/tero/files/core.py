import abc
from typing import Optional

import chardet
from langchain_core.messages import HumanMessage

from ..ai_models import ai_factory
from ..agents.domain import Agent
from ..usage.domain import Usage
from .domain import File


class CurrentQuota:
    def __init__(self, current_usage: float, user_quota: float):
        self.current_usage = current_usage
        self.user_quota = user_quota


class FileQuota:

    def __init__(self, pdf_parsing_usage: Usage, agent: Optional[Agent], current_quota: CurrentQuota):
        self.pdf_parsing_usage = pdf_parsing_usage
        self.current_quota = current_quota
        self.model = ai_factory.build_streaming_chat_model(agent.model_id, agent.model_temperature, agent.model_reasoning_effort) if agent else None
        self.available_tokens = agent.model.token_limit - agent.model.output_token_limit if agent else None

    def has_reached_token_limit(self, text: str) -> bool:
        if not self.model or not self.available_tokens:
            return False

        current_tokens = self.model.get_num_tokens_from_messages(messages=[HumanMessage(content=text)])
        return current_tokens >= self.available_tokens

    def has_reached_quota_limit(self) -> bool:
        return self.current_quota.current_usage + self.pdf_parsing_usage.usd_cost > self.current_quota.user_quota


class BaseFileProcessor(abc.ABC):

    @abc.abstractmethod
    def supports(self, file: File) -> bool:
        pass

    @abc.abstractmethod
    def extract_text(self, file: File, file_quota: FileQuota) -> str:
        pass


class QuotaExceededError(Exception):
    pass


def add_encoding_to_content_type(content_type: Optional[str], content: bytes) -> str:
    # add the encoding to the content type so later on it can be used (for exammple in tools file processing) and is avaible to frontend for proper file visualization
    if content_type and content_type.startswith('text/') and not 'charset=' in content_type:
        detected = chardet.detect(content)
        encoding = detected['encoding'] if detected and detected['encoding'] else 'utf-8'
        content_type = f"{content_type}; charset={encoding.lower()}"
    return content_type or "application/octet-stream"
