"""
Jinja2 template rendering integrated with the application context.
"""
import os
from typing import Dict, Any


class TemplateEngine:
    """Simple template engine with Jinja2 integration."""
    
    def __init__(self, template_folder: str = 'templates'):
        self.template_folder = template_folder
        self._jinja_env = None
    
    @property
    def jinja_env(self):
        """Get or create Jinja2 environment."""
        if self._jinja_env is None:
            try:
                from jinja2 import Environment, FileSystemLoader
                loader = FileSystemLoader(self.template_folder)
                self._jinja_env = Environment(loader=loader, autoescape=True)
            except ImportError:
                # Fallback to simple string replacement if Jinja2 not available
                self._jinja_env = None
        return self._jinja_env
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        if self.jinja_env:
            # Use Jinja2 if available
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        else:
            # Fallback to simple file reading and string replacement
            template_path = os.path.join(self.template_folder, template_name)
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple variable replacement for {{ variable }}
                for key, value in context.items():
                    content = content.replace(f'{{{{{key}}}}}', str(value))
                
                return content
            except FileNotFoundError:
                return f"Template '{template_name}' not found"


def render_template(template_name: str, **context) -> str:
    """Render a template using the current app's template engine."""
    from .context import current_app
    return current_app.template_engine.render_template(template_name, **context)
