# Unit 4: Where Text Chats Probably Live vs Where Files Probably Live

This unit introduces the first major storage architecture split:

- databases for structured records
- object storage for big file/blob payloads

## Two storage jobs

Think of a database as an organized ledger.

It is good for:

- list my recent chats
- search/filter by user or time
- enforce ownership
- link files to conversations
- manage delete/retention workflows

Think of object storage as a giant warehouse for large byte blobs.

It is good for:

- images
- PDFs
- audio
- video
- large file uploads

## Why this split is likely

OpenAI publicly says:

- exports can include a `conversations.json`
- files and chats have related but separately described retention behavior
- files uploaded during a conversation are tied to that conversation's lifecycle

This does not prove the exact internal storage engine, but it strongly supports
the idea that chat records and file blobs are treated as different kinds of
objects.

`Inference`: the normal system design pattern is:

- chat/message/account metadata in a database
- file bytes in object storage
- database rows storing pointers to file objects

## Mental model

A file metadata record could conceptually contain:

- `file_id`
- `user_id`
- `chat_id`
- `created_at`
- `mime_type`
- `size_bytes`
- `storage_key`

The database stores the `map`.
The object store keeps the actual `box of bytes`.

## 10^x comparison

Suppose:

- one file payload is `10 MB = 10^7 bytes`
- one metadata row is `10^3 bytes`

Then:

- `10^7 / 10^3 = 10^4`

So the actual file bytes are about:

- `10,000x` larger than the metadata record describing the file

## Scale example

Suppose there are:

- `10^6 files`
- each averaging `10^7 bytes`

Then file payload storage is:

- `10^6 * 10^7 = 10^13 bytes = 10 TB`

If each metadata row is `10^3 bytes`, then metadata storage is:

- `10^6 * 10^3 = 10^9 bytes = 1 GB`

That means:

- payloads: `10 TB`
- metadata: `1 GB`

This is why large files are usually kept out of the main transactional
database.

## Main takeaway

A strong beginner architecture for ChatGPT-like storage is:

- database for chats, users, settings, timestamps, ownership, file references
- object storage for uploaded file bytes
- links/pointers connecting the two

## Sources

- OpenAI Help: https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data
- OpenAI Help: https://help.openai.com/en/articles/9106926-transferring-conversations-from-1-chatgpt-account-to-another-chatgpt-account
- OpenAI Help: https://help.openai.com/en/articles/8983778-chat-and-file-retention-policies-in-chatgpt
- AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html
- PostgreSQL Docs: https://www.postgresql.org/docs/current/tutorial.html
