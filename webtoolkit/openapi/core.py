import copy
import enum
import typing as t

from pydantic import BaseModel

from . import construct


class APIResponse(BaseModel):
    serializer: type[BaseModel]
    status_code: int = 200
    description: str = ""
    accept: str = "application/json"


class LocationType(str, enum.Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"


class APIParameter(BaseModel):
    serializer: type[BaseModel]
    location: LocationType = LocationType.QUERY


class APIBody(BaseModel):
    serializer: type[BaseModel]
    description: str = ""
    content_type: str = "application/json"


class OpenAPI:
    def __init__(self) -> None:
        self.definition = construct.Definition(paths={}, info=construct.Info(), components=None)

    def add_version(self, version: str) -> None:
        self.definition.openapi = version

    def add_info(self, title: str, version: str, description: str = None) -> None:
        self.definition.info = construct.Info(title=title, version=version, description=description)

    def update_tag(self, name: str, description: str) -> None:
        if self.definition.tags is None:
            return None

        for tag in self.definition.tags:
            if name == tag.name:
                tag.description = description

    def to_api_parameters(self, parameters: list[APIParameter]) -> list[construct.Parameter]:
        results: list[construct.Parameter] = []
        for parameter in parameters:
            serializer = parameter.serializer.schema()
            required = serializer.get("required") or []
            for key, value in serializer["properties"].items():
                results.append(
                    construct.Parameter(
                        name=key, in_=parameter.location, required=True if key in required else False, schema_=value
                    )
                )

        return results

    def to_api_body(self, body: APIBody) -> construct.RequestBody:
        content = construct.Content(schema_={"$ref": f"#/components/schemas/{body.serializer.__name__}"})
        self._update_schema(body.serializer)
        return construct.RequestBody(description=body.description, content={body.content_type: content})

    def to_api_response(self, response: APIResponse) -> dict[int, construct.Response]:
        content = construct.Content(schema_={"$ref": f"#/components/schemas/{response.serializer.__name__}"})
        self._update_schema(response.serializer)
        return {
            response.status_code: construct.Response(
                description=response.description, content={response.accept: content}
            )
        }

    def add_endpoint(
        self,
        methodname: str,
        pathname: str,
        tags: t.Optional[t.List[str]] = None,
        summary: t.Optional[str] = None,
        description: t.Optional[str] = None,
        parameters: t.List[construct.Parameter] = None,
        body: construct.RequestBody = None,
        response: t.Dict[str, construct.Response] = None,
    ) -> None:
        endpoint = construct.Endpoint(summary=summary, description=description)
        endpoint.parameters = parameters
        endpoint.requestBody = body
        endpoint.responses = response
        endpoint.tags = self._add_tags(tags) if tags else None

        path = construct.Path(name=pathname, method={methodname: endpoint})
        if self.definition.paths.get(path.name):
            self.definition.paths[path.name].update(path.method)
            return None

        self.definition.paths.update({path.name: path.method})

    def _update_schema(self, serializer: BaseModel) -> None:
        if serializer.schema().get("definitions"):
            self._update_nested_schema(serializer)
            return None

        if self.definition.components is None:
            self.definition.components = construct.Schemas(schemas={serializer.__name__: serializer.schema()})
        else:
            self.definition.components.schemas.update({serializer.__name__: serializer.schema()})

    def _update_nested_schema(self, serializer: BaseModel) -> None:
        schema = copy.copy(serializer.schema(ref_template="#/components/schemas/{model}"))
        definitions = schema.pop("definitions")

        if self.definition.components is None:
            self.definition.components = construct.Schemas(schemas={serializer.__name__: schema})
        else:
            self.definition.components.schemas.update({serializer.__name__: schema})

        for key, value in definitions.items():
            if self.definition.components is None:
                self.definition.components = construct.Schemas(schemas={key: value})
            else:
                self.definition.components.schemas.update({key: value})

    def _add_tags(self, tags: t.List[str]) -> t.List[str]:
        if self.definition.tags is None:
            self.definition.tags = [construct.Tag(name=tag) for tag in tags]
            return tags

        current_tags: t.List[str] = [current_tag.name for current_tag in self.definition.tags]
        for tag in tags:
            if tag not in current_tags:
                self.definition.tags.append(construct.Tag(name=tag))

        return tags
