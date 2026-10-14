"""Django-style WSGI URL routing and view dispatching framework."""

from .urls import path, re_path, URLPattern, RegexURLPattern
from .http import HttpRequest, HttpResponse, JsonResponse, Http404, Http405
from .views import View, TemplateView, RedirectView
from .wsgi import WSGIApplication, get_wsgi_application

__version__ = '1.0.0'

__all__ = [
    'path',
    're_path', 
    'URLPattern',
    'RegexURLPattern',
    'HttpRequest',
    'HttpResponse',
    'JsonResponse',
    'Http404',
    'Http405',
    'View',
    'TemplateView',
    'RedirectView',
    'WSGIApplication',
    'get_wsgi_application',
]
