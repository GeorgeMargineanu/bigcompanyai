from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model_client import ask_model
from schemas import TOOL_SCHEMAS
from tools import TOOL_REGISTRY
from jsonschema import validate, ValidationError
import uuid
import datetime

app = FastAPI(title="Local LLM Action Server")

class InvokeRequest(BaseModel):
    user_id: str
    prompt: str

@app.post('/invoke')
async def invoke(req: InvokeRequest):
    # Ask model what to do.
    raw = ask_model(req.prompt)

    # Validate that model returned a dict
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="model did not return structured JSON")

    tool = raw.get('tool')
    args = raw.get('args', {})

    if not tool:
        raise HTTPException(status_code=400, detail="model response missing 'tool'")

    if tool not in TOOL_REGISTRY:
        raise HTTPException(status_code=400, detail=f"unknown tool: {tool}")

    # Validate args against schema
    schema = TOOL_SCHEMAS.get(tool)
    if schema:
        try:
            validate(instance=args, schema=schema)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"invalid args: {e.message}")

    # Execute tool (synchronously)
    tool_fn = TOOL_REGISTRY[tool]
    try:
        result = tool_fn(**args)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Audit record
    audit = {
        "id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "tool": tool,
        "args": args,
        "result": result,
        "time": datetime.datetime.utcnow().isoformat() + 'Z'
    }

    # NOTE: persist audit to disk/db in production
    return {"ok": True, "audit": audit}
