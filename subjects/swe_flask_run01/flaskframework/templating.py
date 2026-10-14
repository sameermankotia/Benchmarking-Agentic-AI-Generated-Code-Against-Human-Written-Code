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


class SimpleTemplateEngine:
    """Simple template engine for basic variable substitution."""
    
    def render_template_string(self, source: str, **context) -> str:
        """Render a template string with simple variable substitution."""
        import re
        
        def replace_var(match):
            var_name = match.group(1).strip()
            # Handle nested attributes like user.name
            if '.' in var_name:
                parts = var_name.split('.')
                value = context
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part, '')
                    else:
                        value = getattr(value, part, '')
                return str(value)
            else:
                return str(context.get(var_name, ''))
        
        # Replace {{ variable }} patterns
        result = re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_var, source)
        return result
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template file."""
        template_path = os.path.join(self.template_folder, template_name)
        try:
            with open(template_path, 'r') as f:
                source = f.read()
            return self.render_template_string(source, **context)
        except FileNotFoundError:
            return f"Template {template_name} not found"


class TemplateEngine:
    """Template engine wrapper for Jinja2 with fallback."""
    
    def __init__(self, template_folder: str = 'templates'):
        self.template_folder = template_folder
        self._env = None
        self._simple_engine = None
    
    @property
    def env(self):
        """Lazy-load the Jinja2 environment."""
        if self._env is None:
            if not HAS_JINJA2:
                # Use simple template engine as fallback
                if self._simple_engine is None:
                    self._simple_engine = SimpleTemplateEngine()
                    self._simple_engine.template_folder = self.template_folder
                return self._simple_engine
            
            loader = FileSystemLoader(self.template_folder)
            self._env = Environment(
                loader=loader,
                autoescape=select_autoescape(['html', 'xml'])
            )
        return self._env
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        if HAS_JINJA2:
            template = self.env.get_template(template_name)
            return template.render(**context)
        else:
            return self.env.render_template(template_name, **context)
    
    def render_template_string(self, source: str, **context) -> str:
        """Render a template from a string."""
        if HAS_JINJA2:
            template = self.env.from_string(source)
            return template.render(**context)
        else:
            return self.env.render_template_string(source, **context)


def render_template(template_name: str, **context) -> str:
    """Render a template using the current app's template engine."""
    from .context import current_app
    return current_app.template_engine.render_template(template_name, **context)


def render_template_string(source: str, **context) -> str:
    """Render a template string using the current app's template engine."""
    from .context import current_app
    return current_app.template_engine.render_template_string(source, **context)
