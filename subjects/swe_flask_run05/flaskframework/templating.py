"""
Jinja2 template rendering integrated with application context.
"""
import os
from typing import Dict, Any, Optional


class TemplateEngine:
    """Simple template engine with Jinja2-like functionality."""
    
    def __init__(self, template_folder: str = 'templates'):
        self.template_folder = template_folder
        self._jinja_env = None
    
    def _get_jinja_env(self):
        """Get or create Jinja2 environment."""
        if self._jinja_env is None:
            try:
                import jinja2
                loader = jinja2.FileSystemLoader(self.template_folder)
                self._jinja_env = jinja2.Environment(loader=loader)
            except ImportError:
                # Fallback to simple string replacement if Jinja2 not available
                self._jinja_env = None
        return self._jinja_env
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        env = self._get_jinja_env()
        
        if env is not None:
            # Use Jinja2 if available
            template = env.get_template(template_name)
            return template.render(**context)
        else:
            # Simple fallback implementation
            template_path = os.path.join(self.template_folder, template_name)
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple variable substitution
                for key, value in context.items():
                    content = content.replace(f'{{{{{key}}}}}', str(value))
                
                return content
            else:
                raise FileNotFoundError(f"Template {template_name} not found")


def render_template(template_name: str, **context) -> str:
    """Render a template using the current app's template engine."""
    from .context import current_app
    return current_app.template_engine.render_template(template_name, **context)
