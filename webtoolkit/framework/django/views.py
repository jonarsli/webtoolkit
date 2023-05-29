from django.http import HttpResponse, JsonResponse
from django.urls import reverse

from .core import API


async def openapi_schema(request):
    return JsonResponse(API.openapi.definition.dict(by_alias=True, exclude_none=True))


async def swagger_ui(request):
    url = reverse("openapi-schema-view")
    html_template = """
    <!DOCTYPE html>
        <html lang="en">

        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <meta name="description" content="SwaggerUI" />
            <title>SwaggerUI</title>
            <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css" />
        </head>

        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js" crossorigin></script>
            <script>
                var url = "{url}";
                window.onload = () => {{
                    window.ui = SwaggerUIBundle({{
                        url: url,
                        dom_id: "#swagger-ui",
                    }});
                }};
            </script>
        </body>
        </html>
    """
    return HttpResponse(html_template.format(url=url))
