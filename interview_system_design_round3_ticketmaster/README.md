# Round 3 System Design: Ticketmaster-style System

This folder is a separate reference for your interview prep.

## Files in this folder

- `README.md` - translation + prompt interpretation + quick start
- `SYSTEM_DESIGN_GUIDE.md` - how to solve this in interview format
- `mock_ticketmaster.py` - runnable Python mock
- `test_mock_ticketmaster.py` - unit tests
- `demo.py` - flow demo script

## 1) Translation of your Chinese note

Original:

> 第三轮：系统设计  
> 这一轮应该是做 training，一个笑眯眯的日本大叔 shadow 一个中国小哥。  
> 设计一个 Ticketmaster。  
> 系统设计可以按照 Alex Xu 的套路来，结果小哥说：  
> “我们别浪费时间搞什么 back-of-the-envelope calculation, forget about distributed system。我们梳理好 user flow，画一个各个 component 都有的 diagram 就行了。”  
> 需求如下：  
> 如何 handle 短时间内大量人抢票的场景  
> 如何给买票界面有一个 timeout，超过一定时间没付款怎么处理  
> 票都卖完了怎么处理  
> 如何确保付款的人一定拿得到票  
> 如何实现一个 waitlist，如果有人退票了优先通知 waitlist 上靠前的人

English:

- Round 3: system design.
- This round was likely for training; a smiling Japanese senior was shadowing a Chinese interviewer.
- Design a Ticketmaster-like system.
- You can follow Alex Xu style, but interviewer said:
  - "Let's not waste time on back-of-the-envelope calculations."
  - "Forget distributed-system deep dive."
  - "Let's focus on user flow and a component diagram."
- Requirements:
  1. Handle traffic spikes where many users rush to buy tickets in a short window.
  2. Add checkout timeout; if payment is not completed in time, decide what happens.
  3. Handle sold-out behavior.
  4. Ensure users who successfully pay definitely get tickets.
  5. Build a waitlist; if someone refunds/cancels, notify higher-priority waitlist users first.

## 2) What the prompt is really asking

They are testing whether you can design a **correct ticket allocation flow** under contention.

Core concerns:

1. **Fair admission under burst traffic**
2. **Inventory reservation lifecycle** (hold -> pay -> confirm OR hold expires)
3. **No oversell**
4. **Payment correctness + idempotency**
5. **Fair waitlist backfill**

This is less about deep infra and more about product flow correctness and component interactions.

## 3) Quick run for the Python mock

From this folder:

```bash
python -m unittest test_mock_ticketmaster.py -v
python demo.py
```

## 4) How this mock maps to requirements

Requirement -> Mock behavior:

1. Burst抢票: `VirtualQueue` (`join_rush_queue`, `admit_next_in_queue`)
2. Checkout timeout: `Hold.expires_at` + `process_timeouts`
3. Sold out: `create_hold` returns `reason=sold_out`
4. Paid user guaranteed seat: inventory is reserved at hold creation; successful payment converts hold to purchase
5. Waitlist FIFO: `join_waitlist`, `_offer_to_waitlist_locked` gives earliest entries first

## 5) Recommended study order

1. Read `SYSTEM_DESIGN_GUIDE.md`
2. Read `mock_ticketmaster.py`
3. Run `demo.py`
4. Step through tests in `test_mock_ticketmaster.py`
