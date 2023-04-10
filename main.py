import os
import json
import openai
import time
# from typing import Callable, List, Dict
from functools import partial
from fastapi import FastAPI, Request 
from fastapi.responses import FileResponse, JSONResponse
from asyncio import gather, create_task
import chatgpwe.chroma.chroma_db as Chroma
from chatgpwe.utils.utils import get_ids, llm_run
import chatgpwe.prompts.prompts as Prompt
from uuid import uuid4


# TODO Message people / Check messages
# TODO Workflow expansion on current features 
  # TODO See what help has been offered to different chats
# TODO Friends / Following system
# TODO Private / Private Group chat sharing (all shares are public now)
# TODO Some form of auth (?)


#################################
# CONFIG
#################################

# MODE = "DEBUG"
CHROMA_PATH = "chatgpwe/chroma/persisted_data/chat_data.json"

# Set up OpenAI Client
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Server
app = FastAPI()



#################################
# Routes
#################################

# -------------------------------
#  SHARING CHATS
# -------------------------------

# Share a chat
@app.post("/chats")
async def share_chat(chat: str, req: Request): 
  # debug(req, MODE)
  cid, uid = get_ids(req)
  print(f"SHARE CHAT IDS - CID: {cid}, UID: {uid}")
  create_task(process_share_chat(chat, uid))
  return JSONResponse(content='OK', status_code=200)

async def process_share_chat(chat:str, uid: str):
  label, summary, help_wanted = await gather(
    llm_run(partial(Prompt.label_content, chat)),
    llm_run(partial(Prompt.summarize_content, chat)),
    llm_run(partial(Prompt.is_help_wanted, chat))    
  )
  print(f"LABEL: {label}")
  print(f"SUMMARY: {summary}")
  print(f"HELP WANTED?: {help_wanted}") 
  
  doc_id = uuid4()
  
  collection = Chroma.get_collection('global', CHROMA_PATH)
  collection.add(
    documents=[chat],
    metadatas=[{
      "label": label, 
      "summary": summary, 
      "help_wanted": help_wanted, 
      "user_id": uid,
      "created_at": int(time.time())
    }],
    ids=[str(doc_id)]
  )
  
# Get all of the chats I've shared
@app.get("/chats/{username}")
async def get_my_chats(username: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.get(
    where={"user_id": uid},
    include=["documents"]
  )
  return JSONResponse(content, status_code=200)

# Get recent chats that have been shared
@app.get("/recent_chats")
async def get_chats(req: Request):
  cid, uid = get_ids(req)

  current_time = int(time.time())
  today = current_time - 86400
  
  collection = Chroma.get_collection('global', CHROMA_PATH)
  data = collection.get(
    # query_texts=[chat],
    where={"created_at": {"$gte": today}},
    include=["metadatas"] # "documents"
  )
  print(f"RETRIEVED CONTENT: {data}")
  
  content = []
  for md in data['metadatas']:
    content.append({
      "label": md['label'],
      "summary": md['summary']
    })
  return JSONResponse(content, status_code=200)

# -------------------------------
#  RELATED CHATS
# -------------------------------

# Find relevant chats related to what I'm talking about
@app.get("/chats_related_to")
async def get_chats_related_to(chat: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  data = collection.query(
    query_texts=[chat],
    n_results=2, # this is because otherwise it defaults to 10, and if you don't have 10 records it errors
    include=["metadatas"]
  )
  print(f"RETRIEVED CONTENT: {data}")

  content = []
  for md in data['metadatas']:
    content.append({
      "label": md['label'],
      "summary": md['summary']
    })
  return JSONResponse(content, status_code=200)

# -------------------------------
#  HELPING 
# -------------------------------

# Add help to a chat
@app.post("/help/help_a_chat")
async def give_help_to_a_chat(chat_help: str, helped_chat_id: str, req: Request):
  cid, uid = get_ids(req)
  create_task(process_help_chat(chat_help, helped_chat_id, uid))
  return JSONResponse(content='OK', status_code=200)

async def process_help_chat(chat:str, helped_doc_id: str, uid: str ):
  label, summary, help_wanted = await gather(
    llm_run(partial(Prompt.label_content, chat)),
    llm_run(partial(Prompt.summarize_content, chat)),
    # llm_run(partial(Prompt.is_help_wanted, chat))    
  ) 
  # Generate doc ID
  doc_id = uuid4()

  # TODO get user_id of owner of helped_doc_id

  # Store data
  collection = Chroma.get_collection('global', CHROMA_PATH)
  collection.add(
    documents=[chat],
    metadatas=[{
      "label": label, 
      "summary": summary, 
      "user_id": str(uid),
      "helped_chat_doc_id": str(helped_doc_id),
      "created_at": int(time.time())
    }],
    ids=[str(doc_id)]
  )
  
# Find chats people want help on
@app.get("/help/needs_help")
async def get_chats_which_need_help(chat: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.query(
    query_texts=[chat],
    where={"help_wanted": "True"},
    include=["documents"]
  )
  return JSONResponse(content, status_code=200)

# WIP: Find help that I've been offered 
@app.get("/help/check_help_received")
async def check_help_received(chat: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.get(
    query_texts=[chat],
    where={
      "helped_chat_doc_id": {
        '$eq'str(helped_doc_id), # where the doc_id is made by my user_id
      }
    },
    include=["documents"]

  return JSONResponse(content, status_code=200)




  

  
# ===================
# FRIENDS
# ===================
# Get Friend List
## - Who am I friends with
# @app.get("/friends/{username}")
#  pass

# ===================
# FRIEND::ACTIVTY
# ===================
# Friends Online Now / Recently
## - Which of my friends are online right now?
# @app.post("/friends/{username}/active")
#    pass

# Friend Activity
## - What have my friends been working on recently?
# @app.post("/friends/{username}/activity")
#  pass

# ===================
# FRIEND::INVITE
# ===================
# Invite Friends To System
# @app.post("/friends/{username}/activity")
#  pass

# Invite Friends To Help
## - To help with a project
## - To help with a question
# @app.post("/friends/{username}/activity")
#  pass

# ===================
# FRIEND::REQUESTS
# ===================
# Send Friend Request
## - Follow someone
# @app.post("/follow/{username}")
#  pass

# Review Friend Requests
## - Follow someone
# @app.get("/{username}/friend_requests")
#  pass

# Review Friend Requests
## - Follow someone
# @app.get("/{username}/friend_requests")
#  pass




# ----------------------------------------------------


################################################
# BOILERPLATE
################################################

# OpenAI: App Logo
@app.get("/logo.png")
async def plugin_logo():
  return FileResponse('logo_square.png')

# OpenAI: Plugin API Spec
@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest(request: Request):
  host = request.headers['host']
  with open("ai-plugin.json") as f:
    text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
  return JSONResponse(content=json.loads(text))

# OpenAI: Plugin API Spec
@app.get("/openapi.json")
async def openapi_spec(request: Request):
  host = request.headers['host']
  with open("openapi.json") as f:
    text = f.read().replace("PLUGIN_HOSTNAME", f"https://{host}")
  return JSONResponse(content=text, media_type="text/json")
  
@app.get("/legal")
async def legal_info(request: Request):
  host = request.headers['host']
  with open("legal.txt") as f:
    text = f.read()
  return JSONResponse(content=text, media_type="text/plain")

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=5002)