import abc
import aiofiles
import inspect
import json
from typing import Any, Optional
from urllib.parse import quote

import httpx
from langchain_core.tools import BaseTool, StructuredTool

from .core import AgentTool, StatusUpdateCallbackHandler
from ..core.assets import solve_asset_path


class OpenApiTool(AgentTool, abc.ABC):
    _BODY_LOCATION = "body"
    _api_url: str = ""

    async def build_langchain_tools(self) -> list[BaseTool]:
        api_spec = await self._load_api_spec()
        schemas = api_spec.get("components", {}).get("schemas", {})
        return [
            self._build_langchain_tool(path, method, method_spec, schemas)
            for path, path_spec in api_spec.get("paths", {}).items()
            for method, method_spec in path_spec.items() if self._should_include_operation(path, method)
        ]

    async def _load_api_spec(self) -> dict:
        tool_id = self.id.split("-", 1)[0]
        # Use local files to avoid fetching the spec every run.
        return await self._load_json(f"{tool_id}-api-spec.json")

    async def _load_json(self, filename: str) -> dict:
        async with aiofiles.open(solve_asset_path(filename, inspect.getfile(self.__class__))) as file:
            return json.loads(await file.read())

    def _should_include_operation(self, path: str, method: str) -> bool:
        return True

    def _build_langchain_tool(self, path: str, method: str, method_spec: dict, schemas: dict) -> BaseTool:
        async def call_tool(**arguments: dict[str, Any]) -> str:
            param_type = self._find_unique_parameter_type(method_spec)
            params = {param_type: arguments} if param_type else arguments
            path_params = {key: quote(str(value)) for key, value in params.get("path", {}).items()}
            final_path = path.format(**path_params) if path_params else path
            return await self._invoke_rest_api(method, f"{self._api_url}{final_path}", params.get("query"), params.get("header"), params.get("body"))

        name = f"{self.name}-{method_spec['operationId']}"
        description = f"{self.name} tool that {method_spec['description']}"
        return StructuredTool(
            name=name,
            description=description,
            args_schema=self._build_args_schema(method_spec, schemas),
            coroutine=call_tool,
            callbacks=[StatusUpdateCallbackHandler(name, description=description)],
        )

    async def _invoke_rest_api(self, method: str, url: str, params: Optional[dict] = None, headers: Optional[dict] = None, body: Optional[dict] = None) -> Any:
        headers = headers or {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, params=params, headers=await self._add_auth_headers(headers), json=body)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()

    @abc.abstractmethod
    async def _add_auth_headers(self, headers: dict) -> dict:
        raise NotImplementedError

    def _find_unique_parameter_type(self, method_spec: dict) -> Optional[str]:
        ret = None
        for param in method_spec.get("parameters", []):
            location = param["in"]
            if ret and ret != location:
                return None
            ret = location
        body_schema = self._find_body_schema(method_spec)
        if ret and body_schema:
            return None
        return ret if not body_schema else self._BODY_LOCATION

    def _find_body_schema(self, method_spec: dict) -> Optional[dict]:
        # Currently only supporting JSON body requests.
        return method_spec.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})

    def _build_args_schema(self, method_spec: dict, schemas: dict) -> dict[str, Any]:
        ret = self._build_params_schema(method_spec)
        body_schema = self._find_body_schema(method_spec)
        props = ret["properties"]
        if body_schema:
            props[self._BODY_LOCATION] = body_schema
        input_schemas = [schema for schema in props.values() if schema]
        ret = input_schemas[0] if len(input_schemas) == 1 else ret
        self._refactor_schema_refs(ret, schemas)
        return ret

    def _build_params_schema(self, method_spec: dict) -> dict:
        ret = self._build_empty_schema()
        props = ret["properties"]
        for param in method_spec.get("parameters", []):
            location = param["in"]
            props[location] = props.get(location, self._build_empty_schema())
            location_params = props[location]
            name = param["name"]
            param_schema = param["schema"]
            description = param.get("description")
            if description:
                param_schema["description"] = description
            location_params["properties"][name] = param_schema
            if param.get("required"):
                location_params["required"].append(name)
        return ret

    def _build_empty_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def _refactor_schema_refs(self, schema: dict, schemas: dict):
        refs = set()
        self._collect_and_refactor_schema_refs(schema, schemas, refs)
        if refs:
            schema["$defs"] = {ref: schemas[ref] for ref in refs}

    def _collect_and_refactor_schema_refs(self, schema: dict, schemas: dict, refs: set):
        ref = schema.get("$ref")
        if ref:
            self._refactor_ref(schema, ref.split("/")[-1], schemas, refs)
        self._refactor_subschemas_refs("allOf", schema, schemas, refs)
        self._refactor_subschemas_refs("anyOf", schema, schemas, refs)
        self._refactor_subschemas_refs("oneOf", schema, schemas, refs)
        schema_type = schema.get("type")
        if not schema_type:
            self._handle_schema_without_type(schema, schemas, refs)
        elif schema_type == "array":
            items = schema.get("items")
            if items:
                self._collect_and_refactor_schema_refs(items, schemas, refs)
        elif schema_type == "object":
            for value in schema.get("properties", {}).values():
                self._collect_and_refactor_schema_refs(value, schemas, refs)
            # removing additional properties to simplify schema since so far we haven't identified any use case for them when used by the llm
            if schema.get("additionalProperties"):
                del schema["additionalProperties"]

    def _handle_schema_without_type(self, schema: dict, schemas: dict, refs: set) -> None:
        # Hook for subclasses to handle special schemas lacking a type.
        return None

    def _refactor_ref(self, schema: dict, simple_ref: str, schemas: dict, refs: set):
        schema["$ref"] = f"#/$defs/{simple_ref}"
        # passing refs as parameter and modify it instead of returning it to be able to make this check to avoid infinite recursion in cyclic references
        if simple_ref not in refs:
            refs.add(simple_ref)
            self._collect_and_refactor_schema_refs(schemas[simple_ref], schemas, refs)

    def _refactor_subschemas_refs(self, subschema_key: str, schema: dict, schemas: dict, refs: set):
        for sub_schema in schema.get(subschema_key, []):
            self._collect_and_refactor_schema_refs(sub_schema, schemas, refs)
