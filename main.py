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

# TODO [DEBUG] '/chats/me/help_received' - wonky when you offer help to your own projects
# TODO Message people / Check messages
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

# ROUTE: Share a chat
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
      "created_at": int(time.time()),
      'help_received_count': 0,
    }],
    ids=[str(doc_id)]
  )

# ROUTE: Get a specific chat 
@app.get("/chat")
async def get_chat(chat_id: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.get( ids=[chat_id] )
  return JSONResponse(content=content, status_code=200)
  
# ROUTE: Get all of the chats I've shared
@app.get("/my_chats") 
async def get_my_chats(username: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.get(
    where={"user_id": uid},
    include=["documents", "metadatas"]
  )
  return JSONResponse(content, status_code=200)

# ROUTE: Get chats I've shared on a topic
@app.get("/my_chats_on_topic")
async def get_my_chats_on_topic(chat: str, req: Request):
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.query(
    query_texts=[chat],
    where={"user_id": uid},
  )
  return JSONResponse(content, status_code=200)
  
# ROUTE: Get recent chats that have been shared
@app.get("/recent_chats")
async def get_recent_chats(req: Request):
  cid, uid = get_ids(req)

  current_time = int(time.time())
  today = current_time - 86400
  
  collection = Chroma.get_collection('global', CHROMA_PATH)
  data = collection.get(
    where={"created_at": {"$gte": today}},
    include=["metadatas"]
  )
  print(f"RETRIEVED CONTENT: {data}")
  
  content = []
  count = len(data['ids'])
  for i in range(0, count):
    md = data['metadatas'][i]
    content.append({
      "SYSTEM_ONLY-DO_NOT_DISPLAY_TO_USER": {
        "chat_id": data['ids'][i]
      },
      "label": md['label'],
      # "summary": md['summary']
    })
  return JSONResponse(content, status_code=200)

# -------------------------------
#  RELATED CHATS
# -------------------------------

# ROUTE: Get chats related to what I'm talking / asking about
@app.get("/chats_related_to")
async def get_chats_related_to(chat: str, req: Request):
  # TODO Use an 'output formatter'; chat sometimes thinks the ids are links
  
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  data = collection.query(
    query_texts=[chat],
    n_results=2, # this is because otherwise it defaults to 10, and if you don't have 10 records it errors
    include=["metadatas"]
  )
  print(f"RETRIEVED CONTENT: {data}")
  
  # Chroma TODO: `query` returns nested lists, but `get` does not - why?
  content = []
  count = len(data['ids'][0])
  for i in range(0, count):
    md = data['metadatas'][0][i]
    content.append({
      "SYSTEM_ONLY-DO_NOT_DISPLAY_TO_USER": { 
        "chat_id": data['ids'][0][i]
      },
      "label": md['label'],
    })
    
  return JSONResponse(content, status_code=200)


# -------------------------------
#  HELPING 
# -------------------------------

# TODO: Get ChatGPT to submit what users actually type rather than it's interpretation of what they typed; it expands on what people are saying, which is nice, but not what the default should be
# TODO Find chats with {x} amount of help
# TODO: Add a way to indicate no more help needed
# TODO Specify kind of help you're looking for (ideas, investment, ...)

# ROUTE: Add help to a chat
@app.post("/help/help_a_chat")
async def give_help_to_a_chat(chat_help: str, helped_chat_id: str, req: Request):
  cid, uid = get_ids(req)
  create_task(process_help_chat(chat_help, helped_chat_id, uid))
  return JSONResponse(content='OK', status_code=200)

async def process_help_chat(chat:str, helped_chat_id: str, uid: str ):
  label, summary = await gather(
    llm_run(partial(Prompt.label_content, chat)),
    llm_run(partial(Prompt.summarize_content, chat)),
    # llm_run(partial(Prompt.is_help_wanted, chat)) 
  ) 
  
  collection = Chroma.get_collection('global', CHROMA_PATH)
  
  # -> Get `user_id` of the user who created the chat you're helping
  # -> Get metadata of chat you're helping to (later) increment `help_received_count`
  helped_chat = collection.get(
    ids=[helped_chat_id],
    include=["metadatas"]
  )
  helped_chat_metadata = helped_chat['metadatas'][0]
  helped_user_id = helped_chat_metadata['user_id']
  
  # -> Associate the help contribution to the chat, incl chat creator's user id
  doc_id = uuid4()
  collection.add(
    documents=[chat],
    metadatas=[{
      "label": label, 
      "summary": summary, 
      "user_id": str(uid),
      "helped_chat_doc_id": helped_chat_id,
      "helped_chat_user_id": helped_user_id,
      "created_at": int(time.time())
    }],
    ids=[str(doc_id)]
  )

  # -> Update the help recieving chat's `helps_received_count`
  helped_chat_metadata['help_received_count'] += 1
  collection.update(
    ids=[helped_chat_id],
    metadatas=[helped_chat_metadata]
  )
  
# ROUTE: Find chats people want help on
@app.get("/help/needs_help")
async def get_chats_which_need_help(chat: str, req: Request):
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  
  # Chroma TODO: `where` 'helped_chat_doc_id': included in List
  # Chroma TODO: Add `count_where` / `count_get` top-level accessor method (?)
  
  # -> Find which chats need help
  data = collection.get( # switch this to `query` (?)
    where={"help_wanted": "TRUE"},
    limit=10,
    include=["metadatas"]
  ) 

  content = []
  for i, md in enumerate(data['metadatas']):

    # Manage data inconsistencies
    count = 0
    if 'help_received_count' in md:
      count = md['help_received_count']
    else:
      md['help_received_count'] = 0
      collection.update(
        ids=[data['ids'][i]],
        metadatas=[md]
      ) 

    content.append({
      'user': {
        "label": md['label'],
        "Help Count": count
      },
      'system': {
        "hide fields": ['doc_id'],
        "display_format": {
          "render_as_links": "FALSE",
        },
        "doc_id": data['ids'][i],
        "instructions": "Only render the content of the `user` field. Do not render content as links. Do not expect to render links to the user.",
      }
    })
  content.insert(0, {
    'system': {
      "display_format": "table",
      "instructions":"Render the following data as a table. include columns for all fields in the `user` object even if all entries in `count` are zero. Include a column to indicate the row number"
    }
  })
  return JSONResponse(content, status_code=200)


# ROUTE: See what help a chat has received
@app.get("/help/needs_help/help_received")
async def get_help_received_for_chat(helped_chat_id: str, req: Request):
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)
  content = collection.get( where={ "helped_chat_doc_id": helped_chat_id } )
  return JSONResponse(content, status_code=200)


# ROUTE: Find help that I've been offered 
@app.get("/chats/me/help_received")
async def get_help_received_for_my_chats(req: Request):
  
  # debug(req, MODE)
  cid, uid = get_ids(req)
  collection = Chroma.get_collection('global', CHROMA_PATH)

  data = collection.get(where={ "helped_chat_user_id": uid })

  content = []
  for i, md in enumerate(data['metadatas']):

    # Manage data inconsistencies
    count = 0
    if 'help_received_count' in md:
      count = md['help_received_count']
    else:
      md['help_received_count'] = 0
      collection.update(
        ids=[data['ids'][i]],
        metadatas=[md]
      ) 

  content.append({
    'user': {
      "label": md['label'],
      "Help Count": count
    },
    'system': {
      "hide fields": ['doc_id'],
      "display_format": {
        "render_as_links": "FALSE",
      },
      "doc_id": data['ids'][i],
      "instructions": "Only render the content of the `user` field. Do not render content as links. Do not expect to render links to the user.",
    }
  })
  content.insert(0, {
    'system': {
      "display_format": "table",
      "instructions":"Render the following data as a table. include columns for all fields in the `user` object even if all entries in `Help Count` are zero. Include a column to indicate the row number. Render data for the chat which has recieved help, not the chats offering the help."
    }
  })
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