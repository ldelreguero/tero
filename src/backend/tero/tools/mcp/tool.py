from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from enum import Enum
import logging
from typing import Any, Optional, cast, Mapping
from httpx import HTTPStatusError

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient, SSEConnection
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.shared.session import RequestResponder
from mcp.types import ServerRequest, ClientResult, ServerNotification
from pydantic import AnyHttpUrl
from sqlmodel.ext.asyncio.session import AsyncSession

from ...agents.domain import Agent, AgentToolConfig
from ..core import AgentTool, StatusUpdateCallbackHandler, load_schema
from ..auth import AgentToolOauth, ToolAuthCallback, ToolOAuthCallback, ToolOAuthClientInfoRepository, ToolAuthRepository, ToolAuthToken, ToolAuthTokenType, ToolAuthTokenCallback, ToolAuthTokenRequest, ToolAuthCallbackError, ToolAuthRequestException


MCP_TOOL_ID = "mcp"
logger = logging.getLogger(__name__)


class AuthType(str, Enum):
    OAUTH = "oauth"
    BEARER_TOKEN = "bearerToken"

    @classmethod
    def from_string(cls, value: str) -> "AuthType":
        if value == "oauth":
            return cls.OAUTH
        elif value == "bearerToken":
            return cls.BEARER_TOKEN
        else:
            raise ValueError(f"Invalid auth type: {value}")


class McpTool(AgentTool):
    id: str = MCP_TOOL_ID + "-*"
    name: str = "MCP"
    description: str = "Allows to use a set of tools provided by a MCP server"
    config_schema: dict = load_schema(__file__)
    _oauth: Optional[AgentToolOauth] = None
    _bearer_token: Optional[str] = None
    _server_url: str = ""
    _tools: Optional[list[BaseTool]] = None
    
    def configure(self, agent: Agent, user_id: int, config: dict, db: AsyncSession, thread_id: Optional[int] = None):
        super().configure(agent, user_id, config, db, thread_id)
        self._server_url = config.get("serverUrl", "")
        self.id = MCP_TOOL_ID + "-" + cast(str, AnyHttpUrl(self._server_url).host)
        if self._get_auth_type() == AuthType.OAUTH:
            self._oauth = AgentToolOauth(self._server_url, None, None, agent.id, self.id, user_id, db)

    def _get_auth_type(self) -> AuthType:
        return AuthType.from_string(self.config.get("authType", AuthType.OAUTH.value))

    async def _setup_tool(self, prev_config: Optional[AgentToolConfig]):
        prev_token = await ToolAuthRepository(self.db).find_token(self.user_id, self.agent.id, self.id)
        self._bearer_token = self._get_secret("bearerToken")
        if (prev_config and self.config != prev_config.config 
            or self._get_auth_type() == AuthType.BEARER_TOKEN and prev_token and self._bearer_token 
            and self._bearer_token != prev_token.access_token):
            await self.teardown()
        await self._check_auth()
        await self._save_bearer_token(self._bearer_token, self.db)

    async def teardown(self):
        await ToolAuthRepository(self.db).delete_token(self.user_id, self.agent.id, self.id)
        await ToolOAuthClientInfoRepository(self.db).delete(self.agent.id, self.id)

    async def _check_auth(self):
        try:
            async with self.load():
                pass
        except ToolAuthRequestException:
            if self._get_auth_type() == AuthType.BEARER_TOKEN:
                # Avoid tool oauth request exception asking for a new token (and open an additional dialog in frontend) 
                # and just raise an error so interface knows that originial config was invalid
                raise ToolAuthCallbackError("Invalid bearer token")
            else:
                raise

    @asynccontextmanager
    async def load(self) -> AsyncIterator['McpTool']:
        app_name = cast(str, AnyHttpUrl(self._server_url).host)
        transport = "sse" if self._server_url.endswith("/sse") else "streamable_http"

        async def error_raising_message_handler(
            message: RequestResponder[ServerRequest, ClientResult] | ServerNotification | Exception
        ) -> None:
            if isinstance(message, Exception):
                raise message

        auth_token = await self._get_auth_token()
        base_config: dict[str, Any] = {
            "transport": transport,
            "url": self._server_url,
            "headers": { "Authorization": auth_token } if auth_token else {},
			"session_kwargs": {
                "message_handler": error_raising_message_handler,
                "read_timeout_seconds": timedelta(seconds=30)
            }
        }
        connections: Mapping[str, Any] = {app_name: cast(SSEConnection, base_config) if transport == "sse" else base_config}
        try:
            async with MultiServerMCPClient(connections).session(app_name) as mcp_session:
                tools = await load_mcp_tools(mcp_session)
                # this is required since https://mcp.atlassian.com/v1/sse returns arrays with no items description and openAI doesn't like tool with such schema,
                # same happens with https://browser.mcp.cloudflare.com/sse returning a type object with no properties
                self._tools = self._fix_tools_schemas(tools)
                for tool in self._tools:
                    tool.callbacks = [StatusUpdateCallbackHandler(tool.name, description=tool.description)]
                yield self
        except ExceptionGroup as exception:
            # If a bearer token is present but invalid/expired, the MCP server responds with 401; catch that case here.
            if self._get_auth_type() == AuthType.BEARER_TOKEN \
                and any(isinstance(e, HTTPStatusError) and e.response.status_code == 401 for e in exception.exceptions):
                raise ToolAuthRequestException(ToolAuthTokenRequest(tool_id=self.id, agent_id=self.agent.id))
            else:
                raise
    
    async def _get_auth_token(self) -> Optional[str]:
        auth_type = self._get_auth_type()
        if auth_type == AuthType.BEARER_TOKEN:
            bearer_token = await self._get_bearer_token()
            return f"Bearer {bearer_token}"
        elif auth_type == AuthType.OAUTH:
            oauth = self._get_oauth()
            tokens = await oauth.solve_tokens()
            return f"Bearer {tokens.access_token}" if tokens else None
        else:
            raise ValueError("Invalid Auth Type")

    async def _get_bearer_token(self) -> str:
        if self._bearer_token:
            return self._bearer_token
        token = await ToolAuthRepository(self.db).find_token(self.user_id, self.agent.id, self.id)
        if not token:
            raise ToolAuthRequestException(ToolAuthTokenRequest(tool_id=self.id, agent_id=self.agent.id))
        return token.access_token
    
    def _get_oauth(self) -> AgentToolOauth:
        if not self._oauth:
            raise RuntimeError("MCP tool has not been set up properly")
        return self._oauth

    def _fix_tools_schemas(self, tools: list[BaseTool]) -> list[BaseTool]:
        ret = []
        for tool in tools:
            tool.args_schema = self._fix_schema(tool.args_schema)
            ret.append(tool)
        return ret
    
    def _fix_schema(self, schema: Any) -> Any:
        if isinstance(schema, dict):
            items = schema.get("items", {})
            if schema.get("type") == "array" and not items.get("type"):
                if not items:
                    schema["items"] = {"type": "string"}
                else:
                    schema["items"]["type"] = "string"
                return schema
            elif schema.get("type") == "object" and not schema.get("properties"):
                schema["properties"] = {}
                return schema
            else:
                return { key: self._fix_schema(value) for key, value in schema.items() }
        elif isinstance(schema, list):
            return [self._fix_schema(item) for item in schema]
        else:
            return schema

    async def _save_bearer_token(self, bearer_token: Optional[str], db: AsyncSession):
        if not bearer_token:
            return
        token = ToolAuthToken(
            user_id=self.user_id,
            agent_id=self.agent.id,
            tool_id=self.id,
            access_token=bearer_token,
            token_type=ToolAuthTokenType.BEARER,
            expires_in=None,
            scope=None,
            refresh_token=None,
            expires_at=None
        )
        await ToolAuthRepository(db).save_token(token)
        
    async def build_langchain_tools(self) -> list[BaseTool]:
        if not self._tools:
            raise RuntimeError("MCP tool has not been set up properly")
        return self._tools
    
    async def auth(self, auth_callback: ToolAuthCallback):
        auth_type = self._get_auth_type()
        if auth_type == AuthType.OAUTH:
            state = await ToolAuthRepository(self.db).find_state(self.user_id, self.id, cast(ToolOAuthCallback, auth_callback).state)
            if not state:
                raise ToolAuthCallbackError("OAuth state not found")
            await self._get_oauth().callback(cast(ToolOAuthCallback, auth_callback), state)
        elif auth_type == AuthType.BEARER_TOKEN:
            self._bearer_token = cast(ToolAuthTokenCallback, auth_callback).auth_token
            await self._check_auth()
            await self._save_bearer_token(self._bearer_token, self.db)

    async def clone(self, agent_id: int, cloned_agent_id: int, tool_id: str, user_id: int, db: AsyncSession) -> None:
        pass
