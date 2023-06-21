import functools
import json

from django.core.handlers.asgi import ASGIRequest
from django.http import JsonResponse
from pydantic import BaseModel

from webtoolkit.openapi.core import (
    APIBody,
    APIParameter,
    APIResponse,
    LocationType,
    OpenAPI,
)


class APIRoute(BaseModel):
    url: str
    module: str
    view: str
    cbv: bool


class API:
    openapi = OpenAPI()
    routes: list[APIRoute] = []

    @classmethod
    def parameter(
        cls,
        method: str,
        url: str,
        parameters: list[APIParameter],
        response: APIResponse,
        tags: list[str] = None,
    ):
        def decorator(func):
            summary, description = cls._get_document(func.__doc__)
            api_parameters = cls.openapi.to_api_parameters(parameters)
            api_response = cls.openapi.to_api_response(response)
            cls.openapi.add_endpoint(
                method,
                url,
                tags,
                summary,
                description,
                parameters=api_parameters,
                response=api_response,
            )
            view, cbv = (func.__qualname__.split(".")[0], True) if "." in func.__qualname__ else (func.__name__, False)
            cls.routes.append(APIRoute(url=url, module=func.__module__, view=view, cbv=cbv))

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                request: ASGIRequest = next(filter(lambda arg: isinstance(arg, ASGIRequest), args), None)
                if not request:
                    raise TypeError("ASGIRequest type not found.")

                for parameter in parameters:
                    if parameter.location == LocationType.QUERY:
                        args = args + (parameter.serializer(**request.GET.dict()),)
                    elif parameter.location == LocationType.PATH:
                        args = args + (parameter.serializer(**kwargs),)

                api_response = await func(*args, **kwargs)
                if isinstance(api_response, BaseModel) and response.accept == "application/json":
                    return JsonResponse(json.loads(api_response.json()), status=response.status_code)

                return api_response

            return wrapper

        return decorator

    @classmethod
    def body(
        cls,
        method: str,
        url: str,
        body: APIBody,
        response: APIResponse,
        tags: list[str] = None,
    ):
        def decorator(func):
            summary, description = cls._get_document(func.__doc__)
            api_body = cls.openapi.to_api_body(body)
            api_response = cls.openapi.to_api_response(response)
            cls.openapi.add_endpoint(
                method,
                url,
                tags,
                summary,
                description,
                body=api_body,
                response=api_response,
            )
            view, cbv = (func.__qualname__.split(".")[0], True) if "." in func.__qualname__ else (func.__name__, False)
            cls.routes.append(APIRoute(url=url, module=func.__module__, view=view, cbv=cbv))

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                request: ASGIRequest = next(filter(lambda arg: isinstance(arg, ASGIRequest), args), None)
                if not request:
                    raise TypeError("ASGIRequest type not found.")
                args = args + (body.serializer(**json.loads(request.body)),)

                api_response = await func(*args, **kwargs)
                if isinstance(api_response, BaseModel) and response.accept == "application/json":
                    return JsonResponse(json.loads(api_response.json()), status=response.status_code)

                return api_response

            return wrapper

        return decorator

    @classmethod
    def _get_document(cls, document: str) -> tuple[str, str]:
        if document is None:
            return None, None

        if "\n" in document:
            docs = document.split("\n")
            docs = [doc.strip() for doc in docs]
            return docs[0], "".join(f"{b}\n" for b in docs[1:-1])

        return document, None
