import typing as t

from pydantic import BaseModel, Field


class Schemas(BaseModel):
    schemas: t.Dict[str, t.Any]


class Parameter(BaseModel):
    name: str
    in_: str = Field(alias="in")
    required: bool
    schema_: dict = Field(alias="schema")
    description: t.Optional[str]

    class Config:
        allow_population_by_field_name = True


class Content(BaseModel):
    schema_: t.Dict[str, str] = Field(alias="schema")

    class Config:
        allow_population_by_field_name = True


class Response(BaseModel):
    description: t.Optional[str]
    content: t.Optional[t.Dict[str, Content]]


class RequestBody(BaseModel):
    description: t.Optional[str]
    content: t.Optional[t.Dict[str, Content]]


class Endpoint(BaseModel):
    tags: t.Optional[t.List[str]]
    summary: t.Optional[str]
    description: t.Optional[str]
    requestBody: t.Optional[RequestBody]
    parameters: t.Optional[t.List[Parameter]]
    responses: t.Optional[t.Dict[str, Response]]


class Path(BaseModel):
    name: str
    method: t.Dict[str, Endpoint]


class Tag(BaseModel):
    name: t.Optional[str]
    description: t.Optional[str]


class Info(BaseModel):
    title: str = "OpenAPI"
    version: str = "0.0.1"
    description: t.Optional[str]


class Definition(BaseModel):
    openapi: str = "3.0.0"
    info: t.Optional[Info]
    tags: t.Optional[t.List[Tag]]
    paths: t.Optional[t.Dict[str, t.Any]]
    components: t.Optional[Schemas]
