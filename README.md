# ChatGPWe: A ChatGPT Plugin For Sharing Ideas & Helping Each Other 🥰 

> _Built by [@estill01](https://twitter.com/estill01) during the first-ever **ChatGPT Plugin Hackathon** sponsored by Chroma, OpenAI, Replit, and Retool - SF, 4/8-4/9, 2023_

[www.chatgpwe.com](https://chatgpwe.com)

[ChatGPWe](https://chatgpwe.com) is a ChatGPT Plugin which enables users to share their chats inside ChatGPT and gather helpful ideas from the community. 

ChatGPWe transforms ChatGPT into an environment where people can not only learn and explore their own ideas, but also work together to leverage the collective intelligence of the global ChatGPT community (and those clever AIs 😉) to build ideas, solve problems, and foster a deeper understanding of the world around us. 

This repo is a taste of what's possible when you start to think of ChatGPT as a social product. There are tons of features and refinements possbile from here, but most importantly, hopefully this ChatGPWe gives you a peek at how a world where everyone can interact and work together, turbo-charged by AI this time around, has the potential to a much much better place. Onward into the future.

## ❤️ I Want ChatGPWe!

Send [@ChatGPWe](https://chatgpwe) a Tweet / DM and we'll see if we can't get you hooked up. Or, maybe we can get this thing into the official ChatGPT Plugin store and then you can just add it!


## 🌟 Features

**Broadcast**\
Share your ChatGPT chats to the global ChatGPT community! Transform ChatGPT from a 'single-player' experience into a 'multi-player' one. 

**Discover**\
See what everyone else is talking about. Retrieve your own shared chats, recently shared chats, and chats related to topics you want to explore.

**Help**\
ChatGPWe automatically assesses if shared chats are looking for feedback or help and enables you to share your helpful ideas to those chats.



## 🎯 Chroma Knowledge-Engine And GPT-4 Integration
ChatGPWe was built using the [Replit](https://www.replit.com) web IDE, [OpenAI's](https://platform.openai.com/) GPT-4 API, and the [Chroma](https://www.trychroma.com) knowledge-engine embeddings DB.

### Core Workflow
Once users have installed the ChatGPWe plugin into ChatGPT they can then ask to share their chats with the community, and explore what others have shared.

When users share a chat, the ChatGPWe plugin kicks in and ChatGPT sends your chat off to ChatGPWe. 

The ChatGPWe application then uses GPT-4 to process the chats it receives to generate a `label`, `summary`, and determination of whether the author has expressed any interest in having people `help` on whatever they're talking about.

The generated data is used as metadata for the core chat content, and the bundle is stored in Chroma. Since Chroma converts the data you store in it into embeddings, similarity search is then as trivially easy as performing a basic `query` action with chat content you want to find related chats based on - very cool!

### GPT-4
- Generate brief descriptive label based on chat content
- Summarize shared chat
- Determine if shared chat is interested in or seeking help

### Chroma

- Store chats
- Retrieve chats
- Find related chats

## 📡 API Endpoints

Currently at Hackathon-level implementation (😬) and 'designed' to facilitate auto-genreation of endpoints ChatGPT will successfully figure out what to pick, and when to pick them. This ain't your REST API of yesteryear.. 

`POST /chats`: Share a chat.

`GET /chats/{username}`: Retrieve all shared chats of a user.

`GET /recent_chats`: Get recent shared chats.

`GET /chats_related_to`: Find relevant chats related to a given chat using the Chroma knowledge-engine.

`POST /help/help_a_chat`: Provide help to a chat.

`GET /help/needs_help`: Find chats that need help.

`GET /help/check_help_received`: (WIP) Find help that a user has received.

## 🔮 Future Enhancements

So many! 
- Implement a Friends and Following system to foster connections and collaboration. 👫
- Add DM messaging features. 📨
- Refine and expand Help system 🦾
- Refine data formatting to facilitate exploration 👀
- Add authentication to enable Private Group Chats and other more focused or open discussions. 🔒