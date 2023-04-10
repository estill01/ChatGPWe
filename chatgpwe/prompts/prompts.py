def label_content(content: str) -> str:
  system = {
    'role': 'system',
    'content':
    'generate a very brief but descriptive single sentence label for the provided content. Do not use introductory language to explain what you have done, just return the label text have genreated. If you are unable to generate a label, return an empty string.',
  }
  
  user = {
    'role': 'user',
    'content': f"{content}"
  }

  return [system, user]

def summarize_content(content: str) -> str:
  system = {
    'role': 'system',
    'content':
    'generate a brief summary of the provided content. Do not use introductory language to explain what you have done, just return the summary you have genreated. If you are unable to generate a summary, return an empty string.',
  }
  
  user = {
    'role': 'user',
    'content': f"{content}"
  }

  return [system, user]

def is_help_wanted(content: str) -> str:
  system = {
    'role': 'system',
    'content':
    'Does this text ask for help or otherwise imply that other people could, should, or are invited to help them? Please respond simply either "TRUE", or "FALSE"; do not explain yourself or provide any other output.'
  }
  
  user = {
    'role': 'user',
    'content': f"{content}"
  }

  return [system, user]