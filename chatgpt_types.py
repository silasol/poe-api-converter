import time
from typing import List

from pydantic import BaseModel

import util


class SSEDelta(BaseModel):
    content: str

    def to_dict(self):
        return {
            "content": self.content
        }


class SSEChoice(BaseModel):
    index: int
    delta: SSEDelta
    finishReason: str

    def to_dict(self):
        return {
            "index": self.index,
            "delta": self.delta.to_dict(),
            "finishReason": self.finishReason
        }


class CompletionSSEResponse(BaseModel):
    choices: List[SSEChoice]
    created: int = int(time.time())
    id: str = "chatcmpl-" + util.rand_string_runes(29)
    model: str
    object: str = "chat.completion.chunk"

    def to_dict(self):
        chioces_dict_list = []
        for choice in self.choices:
            chioces_dict_list.append(choice.to_dict())

        return {
            "choices": chioces_dict_list,
            "created": self.created,
            "id": self.id,
            "model": self.model,
            "object": self.object
        }


class GPTRequest(BaseModel):
    stream: bool = False
    model: str = "GPT-4"
    messages: list
    temperature: float = 0.7
