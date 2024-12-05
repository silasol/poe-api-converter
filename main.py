import json
import logging
import os
import sys

import toml
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, StreamingResponse

import poe
from chatgpt_types import CompletionSSEResponse, SSEChoice, GPTRequest, SSEDelta

file_path = os.path.abspath(sys.argv[0])
file_dir = os.path.dirname(file_path)
config_path = os.path.join(file_dir, "config.toml")
config = toml.load(config_path)

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)

need_auth_router = [
    "/chat/completions",
    "/v1/chat/completions",
]


def get_auth_token(request: Request):
    # get authorization token
    authorization: str = request.headers.get("Authorization")
    if authorization:
        token = authorization.replace("Bearer ", "", 1)
        logging.info(f"Extracted Token: {token}")
        return token
    else:
        logging.error("Authorization token not found")
        return None


# https://platform.openai.com/docs/api-reference/models/list
@app.get("/models")
@app.get("/v1/models")
async def get_models():
    models = ["GPT-4"]

    model_data = []

    for model in models:
        model_data.append({
            "id": model,
            "object": "model",
            "created": 0,
            "owned_by": "",
        })

    return {"object": "list", "data": model_data}


# https://platform.openai.com/docs/api-reference/chat/create
@app.post("/chat/completions")
@app.post("/v1/chat/completions")
async def chat_completions(request: Request, gpt_request: GPTRequest):
    # get request body
    token = get_auth_token(request)
    if not token:
        return "Authorization token not found"

    is_stream = gpt_request.stream
    bot_name = gpt_request.model
    temperature = gpt_request.temperature

    req_messages = gpt_request.messages
    poe_messages = []
    for message in req_messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        poe_messages.append(poe.ProtocolMessage(role=role, content=content))

    async def event_stream():
        async for response in poe.stream_get_responses(api_key=token, bot_name=bot_name,
                                                       messages=poe_messages):
            sse_resp = CompletionSSEResponse(
                choices=[
                    SSEChoice(index=0, delta=SSEDelta(content=response), finishReason="completed")
                ],
                model=bot_name
            )

            resp = f"data: {json.dumps(sse_resp.to_dict())}\n\n"
            logging.info(f"Response: {resp}")
            yield resp
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/", response_class=PlainTextResponse)
async def root():
    return "Poe API Converter is running"


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=config.get('port', 5100))
