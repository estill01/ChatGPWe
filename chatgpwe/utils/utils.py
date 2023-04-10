from typing import Callable, List, Dict
from fastapi import Request 
import openai

_CHATS = {}

def debug(req: Request = None, mode: str = None):
  if req and mode == "DEBUG":
    for attr in req:
      print(f"{attr}: {req[attr]}")

def get_ids(req: Request = None):
  if req:
    conversation_id = req.headers.get("openai-conversation-id")
    ephemeral_id = req.headers.get("openai-ephemeral-user-id")
  else: 
    conversation_id = "0"
    ephemeral_id = "0"
  return (conversation_id, ephemeral_id)


async def llm_run(prompt_fn: Callable[[], List[Dict[str, str]]]):
  response = openai.ChatCompletion.create(
    model='gpt-4',
    messages=prompt_fn()
  )
  return response.choices[0].message.content
