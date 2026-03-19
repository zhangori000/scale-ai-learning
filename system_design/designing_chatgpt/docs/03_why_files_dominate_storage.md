# Unit 3: Why Files and Images Dominate Storage Faster Than Chat Text

This unit explains why attachment storage often outgrows conversation storage
much faster than beginners expect.

## Official file-size facts

OpenAI currently documents these caps:

- files can be as large as `512 MB`
- images can be as large as `20 MB`
- spreadsheets can be as large as about `50 MB`
- text/document files can be as large as `2 million tokens`
- per-user file cap is `10 GB`
- per-organization file cap is `100 GB`

## Compare one file with one medium chat

From Unit 2, keep this estimate:

- one medium text conversation ~= `10^5 bytes = 100 KB`

Now compare.

Max image:

- `20 MB ~= 2 * 10^7 bytes`
- `(2 * 10^7) / (10^5) = 2 * 10^2 = 200`

So:

- one max-size image ~= `200` medium chats

Large spreadsheet:

- `50 MB ~= 5 * 10^7 bytes`
- `(5 * 10^7) / (10^5) = 5 * 10^2 = 500`

So:

- one large spreadsheet ~= `500` medium chats

Max file:

- `512 MB ~= 5 * 10^8 bytes`
- `(5 * 10^8) / (10^5) = 5 * 10^3 = 5000`

So:

- one max-size file ~= `5000` medium chats

## A useful surprise about text documents

For English-ish text:

- `1 token ~= 4 bytes`

A `2 million token` document is roughly:

- `2 * 10^6 * 4 = 8 * 10^6 bytes`
- about `8 MB`

So even a huge text document can still be smaller than:

- a `20 MB` image
- a `50 MB` spreadsheet
- a `512 MB` file

This is why binary/visual data often wins the storage battle.

## Use the 10 GB cap for intuition

User cap:

- `10 GB ~= 10^10 bytes`

How many medium chats fit?

- `10^10 / 10^5 = 10^5`
- about `100,000` medium chats

How many max-size images fit?

- `10^10 / (2 * 10^7) = 0.5 * 10^3`
- about `500` max-size images

So:

- around `100,000` medium chats
- or only around `500` big images

This is a strong mental picture to keep.

## Original bytes vs derived data

`Inference`: a production system often stores more than the original file bytes.
It may also create:

- metadata
- extracted text
- previews/thumbnails
- scan outputs
- indexing data

OpenAI's public docs used here do not describe the exact internal persistence
of those artifacts, so treat this as standard systems inference.

## Main takeaway

If a design discussion only talks about conversation rows and ignores uploaded
files, it can under-estimate storage requirements by a lot.

## Sources

- OpenAI Help: https://help.openai.com/en/articles/8555545-file-uploads-faq/
- OpenAI Help: https://help.openai.com/en/articles/10416312-visual-retrieval-with-pdfs-faq
- OpenAI Help: https://help.openai.com/en/articles/8809935-how-to-delete-and-archive-chats-in-chatgpt
- OpenAI Docs: https://platform.openai.com/docs/concepts/tokens
- OpenAI GitHub: https://github.com/openai/tiktoken
