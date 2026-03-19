# Unit 1: What "Storage" Means in ChatGPT

We do not have public documentation for OpenAI's exact internal database or
storage engine choices for ChatGPT. This unit therefore separates:

- `official`: what OpenAI publicly documents
- `inference`: what follows from standard system design patterns

## Four different meanings of "memory"

- `Storage`: long-lived data kept in cloud systems
- `RAM`: short-lived working memory on CPUs
- `VRAM`: short-lived working memory on GPUs
- `ChatGPT Memory`: a product feature that remembers facts about the user

Useful analogy:

- storage = warehouse
- RAM = desk
- VRAM = tool tray attached to the machine doing the work
- ChatGPT Memory = sticky note about the user

## What OpenAI publicly says is stored

OpenAI help docs say:

- chats are saved in the account until deleted
- deleted chats are scheduled for deletion within 30 days, with exceptions
- files uploaded in chats are tied to the chat lifecycle
- files uploaded to GPTs/projects are tied to those objects
- saved memories are stored separately from chat history
- temporary chats do not appear in history and are deleted within 30 days
- consumer users can turn off "Improve the model for everyone"

This already gives at least these user-facing buckets:

- chat history
- uploaded files and images
- saved memories
- account/control settings

`Inference`: any large service also likely stores account metadata, safety
records, logs, and backups. The public docs used here do not expose exact
schemas.

## 10^x math toolbox

- `10^3` = 1,000
- `10^6` = 1,000,000
- `10^9` = 1 billion
- `10^12` = 1 trillion

For rough storage estimation:

- `1 KB ~= 10^3 bytes`
- `1 MB ~= 10^6 bytes`
- `1 GB ~= 10^9 bytes`
- `1 TB ~= 10^12 bytes`

Useful beginner approximation:

- `1 byte ~= 1 English character`

Multiplication rule:

- `10^a * 10^b = 10^(a+b)`

## First estimate

Suppose one medium text conversation stores about:

- `10^5 bytes = 100 KB`

Then:

- `10^6 conversations * 10^5 bytes = 10^11 bytes = 100 GB`
- `10^7 conversations * 10^5 bytes = 10^12 bytes = 1 TB`

Now compare that with one image:

- `20 MB ~= 2 * 10^7 bytes`

Relative to a `100 KB` conversation:

- `(2 * 10^7) / (10^5) = 2 * 10^2 = 200`

So one max-size image can be about the same storage as:

- `200` medium text conversations

## Main takeaway

The first mental correction is:

- storage is not just chats
- storage is chats, files, memories, settings, and other service state

The second mental correction is:

- plain text is often smaller than beginners expect
- files and images grow storage much faster

## Sources

- OpenAI Help: https://help.openai.com/en/articles/8983778-chat-and-file-retention-policies-in-chatgpt
- OpenAI Help: https://help.openai.com/en/articles/8555545-file-uploads-faq
- OpenAI Help: https://help.openai.com/en/articles/8590148-memory-faq
- OpenAI Help: https://help.openai.com/en/articles/7730893-data-controls-faq
