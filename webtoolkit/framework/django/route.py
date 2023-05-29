import importlib

from django.urls import path

from .core import API


def to_urlpatterns():
    urlpatterns = []
    cbv = []
    for route in API.routes:
        view = getattr(importlib.import_module(route.module), route.view)
        if route.cbv and route.view not in cbv:
            urlpatterns.append(path(route.url[1:], view.as_view()))
            cbv.append(route.view)
        else:
            urlpatterns.append(path(route.url[1:], view))
    return urlpatterns
