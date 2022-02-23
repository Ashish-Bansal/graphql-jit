
from typing import Optional
from jinja2 import Environment
from jinja2 import FileSystemLoader
import os

PROJECT_DIR = os.path.dirname((os.path.abspath(__file__)))
_env: Optional[Environment] = None

def get_template_env():
    global _env
    if not _env:
        _env = Environment(loader=FileSystemLoader(searchpath=f"{PROJECT_DIR}/templates/"))
    return _env


def render_template(template_name: str, *args, **kwargs) -> str:
    env = get_template_env()
    template = env.get_template(template_name)
    return template.render(*args, **kwargs)
