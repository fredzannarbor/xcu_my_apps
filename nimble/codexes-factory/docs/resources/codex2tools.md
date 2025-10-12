Vision

One tool to rule them all.

Inputs:

codex books in the following formats:

- pdf*
- docx*
- text
- epub
- markdown

Chunkers:

- complete lines
    - specify beginning and ending lines
    - exclude lines containing keywords
- complete sentences
    - exclude sentences containing keywords
    - specify number of sentences
    - specify minimum and maximum number of words per sentence
- complete paragraphs
    - any number of words
    - minimum & maximum number of words per paragraph
    - exclude paras containing keywords
    - coherent narrative scenes
    - chapters
    - number of tokens
    - number of words
    - whole document
        - text only
        - text and images
        - as docx structured data
        - as pdf structured data

Inputs accepted by generators
  - message input (ChatGPT)
  - string input (GPT-4)
  - multimodal input (DALL-E)
  - image input (DALL-E)
  - audio input (Whisper)
  - structured data (PDF, docx, csv, xlsx, json, xml, html, etc.)

Types of generators:
- classic NLP
  - rule-based (regex)
  - LLM by input mode:
    - string
    - message
    - structured data
    - multimodal
  - LLM by provider
    - OpenAI
    - Google
    - Llama tree
    - Anthropic
    - Aleph Alpha
  - Retrieval-Augmented Generation
    --Llama-index
  
Types of generations:
- chained
- one-shot
- integrative (Llama-index)

Outputs:
- by parts of the book
  - front matter
  - figures
  - tables
  - scenes
  - chapters
  - whole book
  - etc.
- by output mode
  - text
  - json
  - docx
  - pdf
  - markdown
  - image
  


