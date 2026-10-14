"""Django-like WSGI framework."""

from .http import HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseNotAllowed, JsonResponse
from .urls import path, re_path, include, URLPattern, URLResolver
from .views import View, TemplateView, RedirectView
from .wsgi import WSGIApplication, get_wsgi_application

__version__ = '1.0.0'

__all__ = [
    'HttpRequest', 'HttpResponse', 'HttpResponseNotFound', 'HttpResponseNotAllowed', 'JsonResponse',
    'path', 're_path', 'include', 'URLPattern', 'URLResolver',
    'View', 'TemplateView', 'RedirectView',
    'WSGIApplication', 'get_wsgi_application'
]
