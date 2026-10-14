"""
Jinja2 template rendering integrated with application context.
"""

import os
import re
from typing import Dict, Any, Optional
from .context import current_app, g


def _simple_template_render(source: str, **context) -> str:
    """Simple template renderer for when Jinja2 is not available."""
    # Add application context variables
    template_context = {}
    template_context.update(context)
    
    # Add current_app and g to template context if available
    try:
        template_context['current_app'] = current_app
        template_context['g'] = g
    except RuntimeError:
        # Outside application context
        pass
    
    # Simple variable substitution using {{ variable }} syntax
    def replace_var(match):
        var_name = match.group(1).strip()
        # Handle nested attributes like current_app.import_name
        if '.' in var_name:
            parts = var_name.split('.')
            value = template_context.get(parts[0])
            for part in parts[1:]:
                if value is not None:
                    value = getattr(value, part, None)
        else:
            value = template_context.get(var_name, '')
        return str(value) if value is not None else ''
    
    # Replace {{ variable }} patterns
    result = re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_var, source)
    return result


def render_template_string(source: str, **context) -> str:
    """Render a template from a string."""
    try:
        from jinja2 import Template
        
        template = Template(source)
        
        # Add application context variables
        template_context = {}
        template_context.update(context)
        
        # Add current_app and g to template context if available
        try:
            template_context['current_app'] = current_app
            template_context['g'] = g
        except RuntimeError:
            # Outside application context
            pass
        
        return template.render(**template_context)
        
    except ImportError:
        # Fall back to simple template rendering
        return _simple_template_render(source, **context)


def render_template(template_name: str, **context) -> str:
    """Render a template from the templates directory."""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        raise ImportError("Jinja2 is required for template rendering")
    
    # Get template directory from current app
    try:
        app = current_app
        template_folder = getattr(app, 'template_folder', 'templates')
    except RuntimeError:
        # Outside application context, use default
        template_folder = 'templates'
    
    # Create Jinja2 environment
    if os.path.isabs(template_folder):
        loader = FileSystemLoader(template_folder)
    else:
        # Relative to current working directory
        loader = FileSystemLoader(os.path.abspath(template_folder))
    
    env = Environment(loader=loader)
    
    # Load and render template
    template = env.get_template(template_name)
    
    # Add application context variables
    template_context = {}
    template_context.update(context)
    
    # Add current_app and g to template context if available
    try:
        template_context['current_app'] = current_app
        template_context['g'] = g
    except RuntimeError:
        # Outside application context
        pass
    
    return template.render(**template_context)
