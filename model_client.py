import json
import subprocess
import os

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

def ask_model(user_prompt: str):
    """
    Sends a prompt to Ollama and expects a JSON response.
    Returns dict or raises ValueError.
    """
    prompt = f"""
You are an automation assistant that outputs ONLY JSON (a single JSON object).
Available tools:
- create_user(username: str, roles: list[str])
- update_file(path: str, content: str, overwrite: bool)

Return exactly one JSON object like:
{{"tool": "create_user", "args": {{"username":"alice","roles":["dev"]}}}}

User: {user_prompt}
"""
    try:
        proc = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, prompt],
            capture_output=True, text=True, check=True, timeout=30
        )
        output = proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise ValueError(f"ollama run failed: {e.stderr or e.stdout}")
    except Exception as e:
        raise ValueError(f"ollama invocation error: {e}")

    # Extract the first JSON object in the output (robust to extra text)
    start = output.find("{")
    end = output.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"no JSON object found in model output: {output!r}")

    json_str = output[start:end]
    try:
        obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"failed to parse JSON from model output: {e}; raw: {json_str!r}")

    return obj
