# Unit 5: How Deletion Probably Works End to End

This unit is about the difference between:

- disappearing from the user interface now
- actually being deleted from underlying systems over time

## Official facts

OpenAI publicly says:

- deleted chats are removed from view immediately
- they are scheduled for permanent deletion within `30 days`
- exceptions exist for legal/security reasons or previously de-identified data
- files uploaded in a conversation are tied to that conversation's lifecycle
- temporary chats are deleted from systems within `30 days`
- deleting an account triggers deletion of data within `30 days`, with
  exceptions
- saved memories are separate from chat history

## Tombstones

A `tombstone` is a delete marker that says:

- hide this now
- finish cleanup later

`Inference`: OpenAI does not publicly describe a tombstone mechanism, but this
is a standard way to implement "gone from the app now, fully deleted later."

## Likely deletion pipeline

Reasonable system pattern:

1. user presses delete
2. chat disappears from the UI
3. database records are marked deleted or queued
4. background jobs remove dependent records
5. attached file objects are deleted
6. backups age out later
7. by the end of the retention window, normal systems should no longer have the
   account-linked data unless an exception applies

## Why asynchronous deletion makes sense

One "chat" may fan out into many items:

- conversation row
- many message rows
- file-reference rows
- file objects
- index/search entries
- backup copies

So deletion is often a small distributed workflow, not one erase operation.

## Back-of-the-envelope example

Suppose one deleted conversation contains:

- `10^2` messages
- each message record is `10^3 bytes`
- `2` images at `2 * 10^7 bytes` each

Message record bytes:

- `10^2 * 10^3 = 10^5 bytes`

Image bytes:

- `2 * 2 * 10^7 = 4 * 10^7 bytes`

Total:

- about `4 * 10^7 bytes`

The main deletion work by bytes is therefore the files, not the text.

## Why a 30-day window is reasonable

Suppose the system must process:

- `10^8 deletions` in a month

One month is about:

- `3 * 10^1 days`

Per day:

- `10^8 / (3 * 10^1) ~= 3 * 10^6`
- about `3 million deletions/day`

Per second, very roughly:

- `3 * 10^6 / 10^5 ~= 3 * 10^1`
- about `30 deletions/second`

That is large, but not absurd for a major internet service.

## Special cases

Archive:

- archived chats remain stored

Temporary Chat:

- not shown in history
- still retained up to `30 days`

Memory:

- deleting a chat may not delete a separate saved memory
- deleting a saved memory may not delete the original chat

## Main takeaway

"Delete" is usually:

- fast from the product point of view
- delayed from the storage system point of view

## Sources

- OpenAI Help: https://help.openai.com/en/articles/8809935-how-to-delete-and-archive-chats-in-chatgpt
- OpenAI Help: https://help.openai.com/en/articles/8983778-chat-and-file-retention-policies-in-chatgpt
- OpenAI Help: https://help.openai.com/en/articles/8914046-temporary-chat-faq
- OpenAI Help: https://help.openai.com/en/articles/6378407-how-to-delete-your-account
- OpenAI Help: https://help.openai.com/en/articles/8590148-memory-faq
