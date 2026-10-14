"""
Jinja2 template rendering integrated with the application context.
"""

import os
from typing import Dict, Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


class TemplateEngine:
    """Template engine for rendering Jinja2 templates."""
    
    def __init__(self, template_folder: str = 'templates'):
        self.template_folder = template_folder
        self._environment = None
    
    @property
    def environment(self):
        """Get or create the Jinja2 environment."""
        if self._environment is None:
            if not HAS_JINJA2:
                raise RuntimeError("Jinja2 is required for template rendering")
            
            # Create template directory if it doesn't exist
            if not os.path.exists(self.template_folder):
                os.makedirs(self.template_folder)
            
            loader = FileSystemLoader(self.template_folder)
            self._environment = Environment(
                loader=loader,
                autoescape=select_autoescape(['html', 'xml'])
            )
        
        return self._environment
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        template = self.environment.get_template(template_name)
        return template.render(**context)
    
    def render_template_string(self, source: str, **context) -> str:
        """Render a template from a string."""
        template = self.environment.from_string(source)
        return template.render(**context)


def render_template(template_name: str, **context) -> str:
    """Render a template using the current app's template engine."""
    from .context import current_app
    return current_app.template_engine.render_template(template_name, **context)


def render_template_string(source: str, **context) -> str:
    """Render a template string using the current app's template engine."""
    from .context import current_app
    return current_app.template_engine.render_template_string(source, **context)
