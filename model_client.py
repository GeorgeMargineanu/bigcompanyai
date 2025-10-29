import json
import subprocess

def ask_model(user_prompt: str):
    """
    Send a prompt to the local Ollama model and expect JSON output.
    """
    prompt = f"""
    You are an automation assistant that outputs ONLY JSON.
    Based on the user's request, choose a tool and arguments.

    Available tools:
    - create_user(username: str, roles: list[str])
    - update_file(path: str, content: str)

    Return ONLY a JSON object, e.g.:
    {{"tool": "create_user", "args": {{"username": "alice", "roles": ["dev"]}}}}

    User: {user_prompt}
    """

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3", prompt],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()

        # Some models add text around JSON — extract clean JSON
        start = output.find("{")
        end = output.rfind("}") + 1
        json_str = output[start:end]
        return json.loads(json_str)
    except Exception as e:
        return {"error": str(e), "raw_output": result.stdout if 'result' in locals() else ""}
