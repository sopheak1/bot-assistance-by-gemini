# 0001 — ChatId validates non-zero, not positive

**Status:** Accepted
**Date:** 2026-06-25

## Context

`docs/ARCHITECTURE.md` Step 4 specifies that `ChatId` should "wrap raw Telegram
ints, validate positivity," mirroring the same rule given for `TelegramUserId`.

Real Telegram chat ids do not follow that rule uniformly: private chat ids are
positive, but group and supergroup chat ids are **negative** (e.g.
`-1001234567890`). Since the product's entire "Two Rooms" model is built on
binding *group* chats to a domain context, a strict positivity check on
`ChatId` would reject every real group chat the bot is meant to operate in.

## Decision

`ChatId` validates **non-zero** instead of positive. Zero is the one value
Telegram never issues for a chat id, so it remains a useful guard against
obviously-invalid input without rejecting valid negative group/supergroup ids.

`TelegramUserId` is unaffected — Telegram user ids are always positive, so the
architecture doc's original rule is correct and unchanged for that type.

## Consequences

- `ChatId(-1001234567890)` is valid; `ChatId(0)` raises `ValueError`.
- Any future code that assumes `ChatId.value > 0` is wrong and should be fixed,
  not treated as the source of truth.
