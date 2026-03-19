# Unit 6: What Else OpenAI Has to Store Besides Your Chats and Files

This unit expands the storage model beyond "chat text plus attachments."

The right mental model is:

- account/user state
- personalization state
- conversation state
- file/media state
- operational state
- model state

## Account and user state

OpenAI says exports can include:

- chat history
- other relevant account data

OpenAI also exposes settings and controls such as:

- data export
- account deletion
- whether chats improve models

`Inference`: this bucket likely includes account ids, plans, setting values,
timestamps, and session/device metadata.

### Small per user, large in aggregate

Suppose account/settings data per user is:

- `10^4 bytes = 10 KB`

Then for:

- `10^8 users`

storage is:

- `10^4 * 10^8 = 10^12 bytes = 1 TB`

## Personalization state

OpenAI documents separate concepts for:

- Memory
- Reference chat history
- Custom Instructions

OpenAI also says:

- custom instructions are included in export
- custom instructions have a `1500` character limit
- saved memories are separate from chat history
- turning off reference chat history removes remembered info from systems within
  30 days

Approximation:

- `1500 characters ~= 10^3 bytes`

For:

- `10^8 users`

that is:

- `10^3 * 10^8 = 10^11 bytes = 100 GB`

Tiny per user. Still large at internet scale.

## Conversation state

From prior units:

- one text conversation is often around `10^4 to 10^6 bytes`

This bucket scales with:

- number of conversations
- number of messages
- message length

## File and media state

OpenAI documents:

- images up to `20 MB`
- files up to `512 MB`
- text/doc files up to `2 million tokens`

The mobile FAQ also says voice clips used for speech-to-text are not retained
beyond what is needed for transcription, while the transcription can appear in
conversation history.

This is a useful systems lesson:

- some raw media may be temporary
- the derived text can be the thing stored long term

## Operational state

`Inference`: any service like ChatGPT almost certainly needs:

- request logs
- moderation or abuse review records
- queue/job state
- analytics/monitoring events
- search indexes

Why logs can matter:

Suppose:

- one event record is `10^2 bytes`
- there are `10^9 events/day`

Then:

- `10^2 * 10^9 = 10^11 bytes/day = 100 GB/day`

So tiny records can become huge because event counts are massive.

## Model state

A `parameter` is one learned number in the model.
The full set of learned numbers is often called the model `weights`.

This is:

- not user data
- but definitely data the service must store

OpenAI does not publish the parameter count or storage size of private ChatGPT
production models. So we should not pretend to know their exact size.

But OpenAI does publish this for some open-weight models. For example:

- `gpt-oss-120b` has `117B` total parameters
- OpenAI says it fits on a single `80 GB` H100 GPU

Illustrative math:

- `10^11 parameters * 2 bytes ~= 2 * 10^11 bytes = 200 GB`

That is only rough intuition, not a claim about ChatGPT's private model size.

## Different buckets scale differently

- account/settings scale with number of users
- conversations scale with number of messages
- files scale with number and size of uploads
- logs scale with traffic volume
- model weights scale with number and size of models, not directly with users

This is one of the most important system design ideas in the whole track.

## Sources

- OpenAI Help: https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data
- OpenAI Help: https://help.openai.com/en/articles/7730893-data-controls-faq
- OpenAI Help: https://help.openai.com/en/articles/8590148-memory-faq
- OpenAI Help: https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt
- OpenAI Help: https://help.openai.com/en/articles/8914046-temporary-chat-faq
- OpenAI Help: https://help.openai.com/en/articles/7885016
- OpenAI Docs: https://platform.openai.com/docs/models/gpt-oss
- OpenAI Help: https://help.openai.com/en/articles/11870455-openai-open-weight-models-gpt-oss
