# Minimal dangerous tools. DO NOT expose these on an open network.
import os
import json
from typing import Dict, Callable


TOOL_REGISTRY: Dict[str, Callable] = {}


def register(name):
    def _wrap(fn):
        TOOL_REGISTRY[name] = fn
        return fn
    return _wrap


@register('update_file')
def update_file(path: str, content: str, overwrite: bool = False):
    # simple safety: limit to a dedicated directory
    BASE = os.environ.get('WORKSPACE_DIR', '/srv/llm_workspace')
    abs_base = os.path.abspath(BASE)
    joined = os.path.abspath(os.path.join(abs_base, path.lstrip('/')))
    if not joined.startswith(abs_base):
        raise ValueError('path outside workspace')


    if os.path.exists(joined) and not overwrite:
        raise ValueError('file exists and overwrite is false')


    os.makedirs(os.path.dirname(joined), exist_ok=True)
    with open(joined, 'w', encoding='utf-8') as f:
        f.write(content)
    return {"path": joined, "status": "written"}


@register('create_user')
def create_user(username: str, roles: list):
    # Example: write to a local JSON users file
    BASE = os.environ.get('WORKSPACE_DIR', '/srv/llm_workspace')
    users_file = os.path.join(BASE, 'users.json')
    os.makedirs(BASE, exist_ok=True)
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}


    if username in users:
        raise ValueError('user exists')


    users[username] = {"roles": roles}
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)

    return {"username": username, "roles": roles}