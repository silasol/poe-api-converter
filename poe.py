import logging
from typing import List

from fastapi import WebSocket, Form
from fastapi.responses import JSONResponse
from fastapi_poe.client import get_bot_response, get_final_response, QueryRequest
from fastapi_poe.types import ProtocolMessage

client_dict = {}

bot_names = {"Assistant", "ChatGPT-16k", "GPT-4", "GPT-4o", "GPT-4o-Mini", "GPT-4-128k", "Claude-3-Opus",
             "Claude-3.5-Sonnet",
             "Claude-3-Sonnet", "Claude-3-Haiku", "Llama-3.1-405B-T", "Llama-3.1-405B-FW-128k", "Llama-3.1-70B-T",
             "Llama-3.1-70B-FW-128k", "Llama-3-70b-Groq", "Gemini-1.5-Pro", "Gemini-1.5-Pro-128k",
             "Gemini-1.5-Pro-1M", "DALL-E-3", "StableDiffusionXL", "gpt-3.5-turbo-16k", "gpt-3.5-turbo",
             "gpt-4-vision-preview", "gpt-4-turbo-preview", "ChatGPT-4o-Latest", "Claude-3.5-Sonnet-200k",
             "Claude-3-Sonnet-200k", "Gemini-1.5-Pro-2M", "Gemini-1.5-Pro-Search", "Gemini-1.5-Flash",
             "Gemini-1.5-Flash-128k", "Gemini-1.5-Flash-Search", "Qwen2-72B-Instruct-T", "FLUX-dev", "FLUX-pro",
             "FLUX-pro-1.1"}


async def get_responses(api_key, prompt, bot):
    if bot in bot_names:
        message = ProtocolMessage(role="user", content=prompt)
        additional_params = {"temperature": 0.7, "skip_system_prompt": False, "logit_bias": {}, "stop_sequences": []}
        query = QueryRequest(
            query=[message],
            user_id="",
            conversation_id="",
            message_id="",
            version="1.0",
            type="query",
            **additional_params
        )
        return await get_final_response(query, bot_name=bot, api_key=api_key)
    else:
        return "Not supported by this Model"


async def stream_get_responses(api_key: str, messages: List[ProtocolMessage], bot_name: str):
    if bot_name in bot_names:
        try:
            async for partial in get_bot_response(messages=messages, bot_name=bot_name, api_key=api_key):
                yield partial.text
        except GeneratorExit:
            return
    else:
        yield "Not supported by this Model"


async def check_token(token: str):
    if token not in client_dict:
        try:
            ret = await get_responses(token, "Please return “OK”", "Assistant")
            if ret == "OK":
                client_dict[token] = token
                return "ok"
            else:
                return "failed"
        except Exception as exception:
            logging.info("Failed to connect to poe due to " + str(exception))
            return "failed: " + str(exception)
    else:
        return "exist"

async def ask(token: str = Form(...), bot: str = Form(...), content: str = Form(...)):
    await check_token(token)
    try:
        return await get_responses(token, content, bot)
    except Exception as e:
        errmsg = f"An exception of type {type(e).__name__} occurred. Arguments: {e.args}"
        logging.info(errmsg)
        return JSONResponse(status_code=400, content={"message": errmsg})

