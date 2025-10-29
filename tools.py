# tools.py
# Minimal dangerous tools. DO NOT expose these on an open network without auth & approval.
import os
import json
import re
import subprocess
from typing import Dict, Callable

TOOL_REGISTRY: Dict[str, Callable] = {}

# Configure workspace and mode via env vars
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "/srv/llm_workspace")
ALLOW_SYSTEM = os.environ.get("ALLOW_SYSTEM_USER_CREATION", "false").lower() in ("1", "true", "yes")

USERNAME_RE = re.compile(r'^[a-z_][a-z0-9_-]{0,31}$')  # conservative unix username pattern

def register(name):
    def _wrap(fn):
        TOOL_REGISTRY[name] = fn
        return fn
    return _wrap

# Helpers
def _ensure_workspace():
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    return os.path.abspath(WORKSPACE_DIR)

def _user_exists_system(username: str) -> bool:
    try:
        res = subprocess.run(["id", username], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def _user_exists_sandbox(username: str) -> bool:
    users_file = os.path.join(WORKSPACE_DIR, "users.json")
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        return username in users
    except FileNotFoundError:
        return False

@register('update_file')
def update_file(path: str, content: str, overwrite: bool = False):
    """
    Write content into a file under WORKSPACE_DIR only.
    path: relative path (no leading ../ allowed)
    """
    base = _ensure_workspace()
    # Normalize and prevent escaping the workspace
    joined = os.path.abspath(os.path.join(base, path.lstrip("/")))
    if not joined.startswith(base):
        raise ValueError("path outside workspace")
    # Ensure parent exists
    os.makedirs(os.path.dirname(joined), exist_ok=True)
    if os.path.exists(joined) and not overwrite:
        raise ValueError("file exists and overwrite=False")
    with open(joined, "w", encoding="utf-8") as f:
        f.write(content)
    return {"path": joined, "status": "written"}

@register('create_user')
def create_user(username: str, roles: list):
    """
    Two modes:
      - SANDBOX (default): store users in WORKSPACE_DIR/users.json (no system changes)
      - SYSTEM (opt-in): actually call useradd (requires ALLOW_SYSTEM and root/sudo)
    """
    if not isinstance(username, str) or not USERNAME_RE.match(username):
        raise ValueError("invalid username; must match conservative unix pattern")

    if not isinstance(roles, list) or any(not isinstance(r, str) for r in roles):
        raise ValueError("roles must be a list of strings")

    base = _ensure_workspace()
    users_file = os.path.join(base, "users.json")

    if ALLOW_SYSTEM:
        # Create a real system user using useradd
        if _user_exists_system(username):
            raise ValueError("user already exists on system")
        groups = ",".join(roles) if roles else ""
        cmd = ["useradd", "-m"]
        if groups:
            cmd.extend(["-G", groups])
        cmd.append(username)
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"useradd failed: {e.stderr.strip() or e.stdout.strip()}")
        # Optionally, you may also create a sandbox record for auditing
        try:
            try:
                with open(users_file, "r", encoding="utf-8") as f:
                    users = json.load(f)
            except FileNotFoundError:
                users = {}
            users[username] = {"roles": roles, "system_user": True}
            with open(users_file, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2)
        except Exception:
            # don't fail the main result if audit write fails
            pass
        return {"username": username, "roles": roles, "system_user": True}

    else:
        # Sandbox mode — record users in JSON
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)
        except FileNotFoundError:
            users = {}
        if username in users:
            raise ValueError("user exists")
        users[username] = {"roles": roles}
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        return {"username": username, "roles": roles, "system_user": False}
