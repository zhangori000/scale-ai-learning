# Unit 7: What GPUs Actually Do and Why VRAM Matters

This unit introduces the basic `GPU + LLM` serving picture.

Main idea:

- storage keeps the model at rest
- VRAM holds the model while it is serving requests
- the GPU uses those weights to compute the next token

## CPU vs GPU

Beginner picture:

- CPU = a few strong workers
- GPU = a huge team of workers doing similar math in parallel

For LLM inference, the GPU mainly performs an enormous number of numeric
operations such as matrix multiplications.

## What VRAM is

VRAM is memory attached directly to the GPU.

Useful analogy:

- SSD = warehouse
- RAM = office shelf
- VRAM = tool tray on the machine that is doing the work

VRAM is different from:

- SSD/object storage
- CPU RAM

## What sits in VRAM during inference

VRAM usually holds at least:

- model weights
- temporary activations
- per-request working memory

The per-request working memory is often called the `KV cache`, but it is enough
for now to know:

- not all VRAM is for weights
- long conversations can consume more working memory

## Why weights need to be close to the GPU

The model repeatedly reuses its weights for many layers and many generated
tokens. If those weights were fetched from slower places during generation,
latency would be much worse.

Concrete numbers from NVIDIA's H100 page:

- H100 memory bandwidth: `3.35 TB/s = 3.35 * 10^12 bytes/s`
- H100 PCIe bandwidth: `128 GB/s = 1.28 * 10^11 bytes/s`

Ratio:

- `(3.35 * 10^12) / (1.28 * 10^11) ~= 26`

So local H100 memory bandwidth is about:

- `26x` higher than that PCIe path

This is the key locality lesson.

## What happens during one chat request

NVIDIA's LLM inference overview breaks the path into:

- tokenization
- prefill
- decode
- de-tokenization

Very simplified flow:

1. prompt text is tokenized
2. prompt tokens enter the model
3. `prefill`: the model processes the full prompt
4. `decode`: the model generates one token at a time
5. output tokens are turned back into text

`Inference`: in a production serving system, the model is normally kept resident
in VRAM rather than being reloaded from disk for every request.

## Back-of-the-envelope bandwidth math

Suppose a model footprint in VRAM is:

- `80 GB = 8 * 10^10 bytes`

Using H100 local memory bandwidth:

- `3.35 * 10^12 bytes/s`

Best-case lower bound to sweep through `80 GB` once:

- `(8 * 10^10) / (3.35 * 10^12) ~= 2.4 * 10^-2 s`
- about `24 ms`

If you instead had to move that `80 GB` over `128 GB/s` PCIe:

- `(8 * 10^10) / (1.28 * 10^11) ~= 6.25 * 10^-1 s`
- about `625 ms`

This is a rough toy estimate, but the core point is solid:

- local VRAM access is much better than repeatedly reaching elsewhere

## Parameter count and bytes

Useful rough rule:

- `model bytes ~= parameters * bytes per parameter`

Toy examples:

- `10^10 params * 2 bytes = 2 * 10^10 bytes = 20 GB`
- `10^11 params * 2 bytes = 2 * 10^11 bytes = 200 GB`

This is why large models can exceed a single GPU.

## Why parameter count is not the whole story

OpenAI's public `gpt-oss-120b` docs say:

- `117B` total parameters
- about `5.1B` active parameters
- fits on a single `80 GB` H100 GPU

This introduces two advanced ideas:

- `precision`: parameters do not all need the same bytes/representation
- `Mixture-of-Experts (MoE)`: not every parameter is active on every token

The main lesson for now is:

- parameter count alone does not fully determine runtime VRAM needs

## Main takeaway

To answer one chat message, the system needs:

- the model weights available to the GPU
- enough VRAM for working state
- enough memory bandwidth to repeatedly read model data fast

This is a large part of what people really mean when they say:

- "LLMs need GPUs"

## Sources

- OpenAI Docs: https://platform.openai.com/docs/models/gpt-oss
- OpenAI Help: https://help.openai.com/en/articles/11870455-openai-open-weight-models-gpt-oss
- OpenAI GitHub: https://github.com/openai/gpt-oss
- NVIDIA: https://www.nvidia.com/en-us/glossary/ai-inference/
- NVIDIA: https://www.nvidia.com/en-us/data-center/h100/
