from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from model_client import ask_model
from schemas import TOOL_SCHEMAS
from tools import TOOL_REGISTRY
from jsonschema import validate, ValidationError
import uuid
import datetime


app = FastAPI()


class InvokeRequest(BaseModel):
    user_id: str
    prompt: str


@app.post('/invoke')
async def invoke(req: InvokeRequest):
    # 1) Ask model what to do. We expect the model to respond with JSON: {"tool":"tool_name", "args": {...}, "explain": "optional explanation"}
    raw = ask_model(req.prompt)


    # Model returns parsed JSON object (dict) or raises ValueError
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="model did not return structured JSON")


    tool = raw.get('tool')
    args = raw.get('args', {})


    if tool not in TOOL_REGISTRY:
        raise HTTPException(status_code=400, detail=f"unknown tool: {tool}")


    # 2) Validate args against schema
    schema = TOOL_SCHEMAS.get(tool)
    try:
        validate(instance=args, schema=schema)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"invalid args: {e.message}")


    # 3) Execute tool (synchronously here)
    tool_fn = TOOL_REGISTRY[tool]
    try:
        result = tool_fn(**args)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    # 4) Build audit record
    audit = {
    "id": str(uuid.uuid4()),
    "user_id": req.user_id,
    "tool": tool,
    "args": args,
    "result": result,
    "time": datetime.datetime.utcnow().isoformat() + 'Z'
    }


    # you should save the audit record to a durable log here


    return {"ok": True, "audit": audit}