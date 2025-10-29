# Example using llama-cpp-python. Swap this out for your favorite local runtime.
import json
import os
from llama_cpp import Llama


MODEL_PATH = os.environ.get('MODEL_PATH', '/models/ggml-model.bin')
llm = Llama(model_path=MODEL_PATH)


# We expect the model to output a JSON object. Use a prompt that constrains output to JSON.
PROMPT_TEMPLATE = '''You are an assistant that outputs exactly one JSON object describing which tool to call.


Respond with ONLY valid JSON and nothing else. The object should have the fields:
- tool: string
- args: object
- explain: optional string


Available tools: create_user, update_file


User request: "{user_prompt}"


Return JSON now.'''




def ask_model(user_prompt: str):
    prompt = PROMPT_TEMPLATE.format(user_prompt=user_prompt)
    # This instruction tuning hyperparameters are minimal; tweak them in real deployment
    out = llm(prompt, max_tokens=256, temperature=0.0)
    text = out['choices'][0]['text']
    # Try to parse JSON; allow the model to sometimes include backticks by stripping
    text = text.strip()
    # Some models prefix with ```json ... ``` — remove fences
    if text.startswith('```'):
        # remove triple fence and optional language
        parts = text.split('```')
    if len(parts) >= 2:
        text = parts[1].strip()


    try:
        obj = json.loads(text)
    except Exception as e:
        raise ValueError('failed to parse JSON from model output: ' + repr(text))
    return obj