# Architecture Design — Life-Sync Telegram Bot

**Status:** Design only — no code generated.
**Source requirements:** `docs/SYSTEM_REQUIREMENTS.md`
**Horizon:** Designed to be maintainable for 3+ years, starting at personal-project scale.

---

## Step 1 — Requirement Analysis

### Core business domains
| Domain | Responsibility |
|---|---|
| **Project Management** | CRUD on projects |
| **Task Management** | CRUD on tasks, status transitions, rollover/defer logic |
| **Habit Tracking** | Habit CRUD, daily check-ins, streak calculation |
| **Reporting** | Read-only aggregation of task/habit history over time windows |
| **Chat Context Routing** | Binding a `chat_id` to a domain (`WORK` vs `HABIT`) |
| **Scheduling / Proactive Messaging** | Daily standup, day-rollover cutoff job |

### Actors
- **End user** — the human in a Telegram group chat.
- **Telegram Bot API** — inbound (updates) and outbound (sendMessage) actor.
- **Scheduler** — internal system actor firing time-based jobs (standup, rollover).
- *(Implicit, under-specified)* — other human members who may be present in the same group chat but aren't the bot's owner. See risk below.

### Integrations
- Telegram Bot API (only external integration in scope today).
- Reserved extension point for future integrations (calendar, LLM summarizer, etc.) — none in scope now.

### Scheduled / background jobs
- **Daily Standup** — per-chat configurable time (default 9:00 AM).
- **Day Rollover** — global cutover time (default 2:00 AM) that decides which calendar day a late-night habit check-in belongs to.

### External APIs
- Telegram Bot API only.

### Data storage requirements
- "Local SQLite `.db` files in `data/`" — **decided:** one file per Telegram user (`telegram_id`), see Step 8.
- Default timezone: **UTC+7 (`Asia/Phnom_Penh`)**, overridable per user.
- Daily Standup time and Day Rollover time are **per-user configurable** (not a single global cron time) — see Steps 4, 6, 7, 8.

### Security concerns
- Strict isolation by `chat_id` + Telegram user id.
- Bot token secrecy.
- Mandatory confirmation before destructive actions (delete project/task) — already specified, good practice.
- **Gap:** no access-control rule for *other* humans who might be present in a "Work" or "Habit" group chat. Anyone in the group can currently invoke mutating commands.

### Future extensibility points
- New domains beyond Task/Habit (Finance, Notes, Goals…).
- Multiple chats per domain context.
- Calendar/external integrations.
- Web dashboard or REST API reusing the same application layer.
- SQLite → PostgreSQL migration as usage grows.
- Long-polling → webhook migration for cloud deployment.

### Requirement weaknesses worth challenging
1. **Storage partitioning — resolved.** Confirmed: one SQLite file per `telegram_id`. This still leaves one open sub-problem — see Step 8 — namely that a scheduler job or an incoming message in a chat must resolve `chat_id → owning telegram_id` *before* it knows which file to open, and a per-user file can't answer that question about itself. A small shared routing registry is required regardless of the per-user file decision; Step 8 covers it.
2. **Timezone model — resolved.** Default `Asia/Phnom_Penh` (UTC+7) for every new user, stored per-user and overridable. Daily Standup and Day Rollover times are likewise per-user settings, not global config — see Steps 4, 6, 7, 8.
3. **No access control within a group chat.** The "Two Rooms" design assumes the group is single-occupant in practice, but Telegram groups are inherently multi-member. Recommend an explicit rule: only the user who ran `/init_work` or `/init_habit` (the "owner") may run mutating commands in that chat — everyone else gets a polite read-only or "not authorized" response.
4. **Deadline optionality is unspecified.** Is a task deadline mandatory? Real task lists need a "someday/no deadline" bucket. Recommend making `Deadline` nullable in the domain model regardless of final product decision — it's a strictly safer default.
5. **No delivery-failure handling.** If the bot is blocked by the user, kicked from a group, or hits a Telegram rate limit during the daily standup push, what happens? Recommend the standup job treats per-chat delivery as independent and failure-isolated (one failing chat must not abort the batch), with failures logged and retried with backoff.
6. **Status enum has no defined transition rules.** `To Do → In Progress → Done` — can a Done task go back to In Progress? Not specified. Recommend keeping transitions permissive for v1 but centralizing the rule in one place (a Value Object) so tightening it later is a one-line change, not a grep-and-fix across the codebase.

None of these block starting the build — they're flagged so the domain model bakes in the right seams (nullable fields, owner concept, timezone field) now rather than as painful migrations later.

---

## Step 2 — Architecture Recommendation

### Recommendation: Modular Monolith, internally structured with Clean Architecture / Hexagonal (Ports & Adapters), organized by DDD bounded contexts

**Why this fits:**
- Single deployable, single maintainer, personal-server-now/cloud-later — full microservices would be solving a team/ops problem this project doesn't have.
- The SRD's own explicit constraint ("business logic separated from Telegram-specific implementation") *is* the Hexagonal Architecture definition: Telegram is a **driving adapter** (inbound), SQLite/scheduler/notifier are **driven adapters** (outbound). Domain code never imports `aiogram` or `sqlalchemy`.
- DDD is applied at a **pragmatic, lite level** — bounded contexts (Projects, Tasks, Habits, Reporting, Chat Context) give the project clean seams for future splitting, without going as far as full event sourcing or deep aggregate trees the domain doesn't need.
- A **modular monolith** lets every bounded context be physically separated in code today and *literally* extracted into its own service later (because it already only talks to other contexts through application-layer interfaces, never reaching into another context's domain/infrastructure).

**Advantages:**
- Domain and application layers have zero framework dependency → fast, deterministic unit tests with no Telegram or DB in the loop.
- Swapping `aiogram` for another bot framework, or adding a second UI surface (web dashboard) later, touches only the adapter layer.
- New bounded contexts (e.g. a future "Finance" domain) are additive — no risk of trampling existing modules.
- Ports around DB, scheduler, cache, and clock give each future scaling bottleneck (Step 13) an isolated, additive migration path.

**Trade-offs:**
- More upfront ceremony (interfaces, DTOs, mapping) than a quick script — slower to ship the very first command.
- Risk of over-engineering for a solo/personal project if every trivial dependency gets a port. Mitigation: only create a port at *real* architectural boundaries — Telegram, Persistence, Scheduler, Notifier, Clock, Cache. Don't wrap things like `datetime` formatting helpers behind interfaces.
- SQLite's "individual files" storage model (Step 8) adds genuine infrastructure complexity (a routing layer) that wouldn't exist with a single Postgres instance — accepted as the cost of following the SRD's stated storage choice while keeping the option to migrate later.

**Alternatives considered and rejected (with reasons):**
- **Pure Hexagonal, no DDD modeling:** Would work mechanically, but habit-streak/day-rollover logic is genuinely tricky business logic that benefits from being named, isolated, and heavily unit-tested as a domain service — worth the small extra DDD vocabulary.
- **Microservices:** Rejected — wrong scale; one maintainer, one bot process, no team to operate independent deployments. Pure premature optimization.
- **Simple layered MVC (router → service → ORM model, Django-style):** Conceptually similar to what's built here, but typically lacks enforced dependency-inversion (services often import ORM models directly), which would let persistence concerns leak into business logic. Clean Architecture's strict inward-pointing dependency rule is the main thing this buys over a naive layered app.
- **Full Event-Driven / CQRS+Event Sourcing:** Overkill for this scale and adds substantial operational complexity (event store, replay logic) with no corresponding requirement. **Compromise adopted:** a lightweight **in-process domain event bus** (e.g. `HabitCheckedInEvent`, `TaskCompletedEvent`) for decoupling cross-cutting reactions (streak updates, future analytics) without a real event store or message broker.

---

## Step 3 — Project Structure

```
telegram-bot-life-sync-assistant/
├── src/
│   └── lifesync/
│       ├── main.py                        # entrypoint: builds bot, registers handlers, starts scheduler
│       ├── bootstrap.py                   # composition root — manual DI wiring of repos/use-cases/adapters
│       │
│       ├── config/
│       │   ├── settings.py                # pydantic-settings typed config
│       │   └── logging_config.py          # structlog/JSON logging setup
│       │
│       ├── shared_kernel/                 # primitives shared by ALL bounded contexts (kept tiny on purpose)
│       │   ├── domain/
│       │   │   ├── value_objects.py       # ChatId, TelegramUserId, DateRange, DomainContext (WORK | HABIT)
│       │   │   ├── exceptions.py          # DomainError base class
│       │   │   ├── clock.py               # Clock port — never call datetime.now() directly elsewhere
│       │   │   ├── random_provider.py     # RandomProvider port — never call random.choice() directly elsewhere
│       │   │   └── events.py              # DomainEvent base + in-process EventBus interface
│       │   └── application/
│       │       └── unit_of_work.py        # UnitOfWork port (transaction boundary abstraction)
│       │
│       ├── projects/                      # Bounded Context: Project Management
│       │   ├── domain/
│       │   │   ├── entities.py            # Project (Aggregate Root)
│       │   │   ├── value_objects.py       # ProjectName
│       │   │   ├── repository.py          # ProjectRepository (Protocol/port)
│       │   │   └── exceptions.py
│       │   ├── application/
│       │   │   ├── use_cases/             # create_project.py, rename_project.py, delete_project.py, list_projects.py
│       │   │   └── dto.py
│       │   └── infrastructure/
│       │       └── sqlite_project_repository.py
│       │
│       ├── tasks/                         # Bounded Context: Task Management
│       │   ├── domain/
│       │   │   ├── entities.py            # Task (Aggregate Root) — holds project_id by reference, not nested
│       │   │   ├── value_objects.py       # TaskStatus, Deadline, ShortDescription
│       │   │   ├── services.py            # RolloverService — pure logic, no I/O
│       │   │   ├── repository.py
│       │   │   └── exceptions.py
│       │   ├── application/
│       │   │   ├── use_cases/             # create_task.py, update_task.py, delete_task.py, list_tasks.py,
│       │   │   │                          # rollover_unfinished_tasks.py, defer_task.py
│       │   │   └── dto.py
│       │   └── infrastructure/
│       │       └── sqlite_task_repository.py
│       │
│       ├── habits/                        # Bounded Context: Habit Tracking
│       │   ├── domain/
│       │   │   ├── entities.py            # Habit (Aggregate Root), HabitCheckIn
│       │   │   ├── value_objects.py       # HabitType, Streak
│       │   │   ├── services.py            # StreakCalculationService — highest-risk logic, heaviest test coverage
│       │   │   ├── repository.py
│       │   │   └── exceptions.py
│       │   ├── application/
│       │   │   ├── use_cases/             # create_habit.py, check_in_habit.py, get_habit_report.py,
│       │   │   │                          # list_habits_for_standup.py
│       │   │   └── dto.py
│       │   └── infrastructure/
│       │       └── sqlite_habit_repository.py
│       │
│       ├── reporting/                     # Read-only Bounded Context — CQRS-lite "query side"
│       │   ├── application/
│       │   │   ├── use_cases/generate_task_report.py
│       │   │   └── dto.py
│       │   └── infrastructure/
│       │       └── sqlite_report_query_service.py   # hand-tuned SQL, bypasses full repository for perf
│       │
│       ├── chat_context/                  # Bounded Context: chat_id → domain-context binding
│       │   ├── domain/
│       │   │   ├── entities.py            # ChatBinding (uses DomainContext from shared_kernel)
│       │   │   └── repository.py          # ChatBindingRepository — backed by the shared registry file
│       │   ├── application/
│       │   │   └── use_cases/             # bind_chat_to_context.py, resolve_chat_context.py
│       │   └── infrastructure/
│       │       └── sqlite_chat_binding_repository.py
│       │
│       ├── users/                         # Bounded Context: per-user settings (lives in the shared bot.db, see Step 8)
│       │   ├── domain/
│       │   │   ├── entities.py            # UserSettings (Aggregate Root)
│       │   │   ├── value_objects.py       # Timezone, StandupTime, RolloverTime
│       │   │   └── repository.py          # UserSettingsRepository
│       │   ├── application/
│       │   │   └── use_cases/             # register_user.py, update_standup_hour.py,
│       │   │                              # update_rollover_hour.py, update_timezone.py, get_user_settings.py
│       │   └── infrastructure/
│       │       └── sqlite_user_settings_repository.py   # backed by the shared bot.db, not the per-user file
│       │
│       ├── quotes/                        # Bounded Context: motivational content, owned by the bot, not per-user
│       │   ├── domain/
│       │   │   └── entities.py            # Quote (id, text, domain_context, sequence_index) — immutable
│       │   ├── application/
│       │   │   └── use_cases/get_motivational_quote.py   # deterministic day-of-year rotation, reads in-memory cache
│       │   └── infrastructure/
│       │       └── sqlite_quote_provider.py   # loads all 200 rows from bot.db once at startup, caches in memory
│       │
│       ├── standup/                       # Cross-context composition layer (orchestrates tasks/habits + a quote)
│       │   └── application/
│       │       └── use_cases/generate_standup.py    # talks only to other contexts' use cases, never their internals
│       │
│       ├── scheduling/                    # Cross-cutting: background job orchestration
│       │   ├── application/
│       │   │   ├── jobs/                  # daily_standup_job.py, day_rollover_job.py
│       │   │   └── scheduler_port.py
│       │   └── infrastructure/
│       │       └── apscheduler_adapter.py
│       │
│       ├── notifications/                 # Cross-cutting: outbound push port
│       │   ├── application/notifier_port.py
│       │   └── infrastructure/telegram_notifier.py
│       │
│       ├── telegram/                      # Driving adapter — THE ONLY place that imports the bot framework
│       │   ├── bot.py                     # dispatcher/bot construction
│       │   ├── middleware/                # chat_context_middleware.py, error_handling_middleware.py,
│       │   │                              # logging_middleware.py, authorization_middleware.py
│       │   ├── handlers/                  # projects/, tasks/, habits/, reporting/, chat_setup/
│       │   ├── conversations/             # FSM wizard definitions (create_project_wizard.py, etc.)
│       │   ├── keyboards/                 # InlineKeyboardMarkup builders
│       │   └── presenters/                # DTO → Telegram message text/markup formatting
│       │
│       └── persistence/                   # Shared infra plumbing used by all *_repository.py implementations
│           ├── db.py                      # engine/session factory + BotDbRouter/UserFileRouter (see Step 8)
│           ├── bot_db.py                  # the bot's own shared file: chat_bindings, user_schedule, quotes
│           ├── models/                    # SQLAlchemy ORM models, explicitly mapped — never the domain entities
│           └── migrations/                # Alembic versions (one history for bot.db, one for per-user files)
│
├── tests/                                 # mirrors src/lifesync 1:1 — see Step 9
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── contract/
│   ├── fakes/                             # shared in-memory fake repos/ports reused across test layers
│   └── conftest.py
│
├── docs/
│   ├── SYSTEM_REQUIREMENTS.md
│   ├── ARCHITECTURE.md                    # this document
│   ├── adr/                               # Architecture Decision Records — one file per significant decision
│   └── diagrams/
│
├── scripts/
│   ├── run_bot.sh
│   ├── run_migrations.sh
│   ├── seed_quotes.py                     # one-time/upgrade seed of the 200 quotes into bot.db
│   └── seed_dev_data.py
│
├── deployments/
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   └── systemd/
│       └── lifesync-bot.service
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── data/                                  # gitignored — runtime SQLite files: bot.db + users/<telegram_id>.db
├── .env.example
├── pyproject.toml
├── README.md
└── CHANGELOG.md
```

### Why each top-level folder exists
- **`src/lifesync/`** — `src/`-layout prevents accidentally importing the package from the repo root during tests; forces installed-package import semantics, the standard for installable Python packages.
- **Per-context folders (`projects/`, `tasks/`, `habits/`, `reporting/`, `chat_context/`, `users/`, `quotes/`)** — each is a DDD bounded context with its own `domain/ → application/ → infrastructure/` stack. This is the primary mechanism for low coupling: a context never imports another context's `domain` or `infrastructure`, only its `application` use cases/DTOs (or not at all).
- **`shared_kernel/`** — deliberately small. Only things genuinely shared everywhere (IDs, Clock, base exceptions, event bus) belong here. If this folder starts accumulating business logic, that's a smell that something should have its own bounded context instead.
- **`quotes/`** — deliberately one of the simplest bounded contexts in the project: the 100 work-quotes and 100 habit-quotes are content the bot itself owns and serves identically to everyone, so they're seeded once into the shared `bot.db` (Step 8) rather than duplicated per user. It still gets domain/application/infrastructure layering (so Telegram/standup depend on an interface, not a hardcoded list), but there's no per-user partitioning, no user-facing mutation — only a one-time/upgrade seed script.
- **`standup/`** — exists because the Daily Standup feature is, per chat, single-domain (a `WORK` chat's standup shows task rollover; a `HABIT` chat's standup shows habit check-ins) plus one motivational quote for that domain. The *orchestration* of "which domain's data to pull, which quote to attach, and how to render today's message" is a separate concern from either domain's core CRUD logic. A thin dedicated module keeps `tasks/`, `habits/`, and `quotes/` ignorant of each other and of the scheduler.
- **`users/`** — holds per-user preferences (timezone, standup time, rollover time) as their own small bounded context, separate from `chat_context/` (which only maps `chat_id → domain_context`). Splitting these matters because a `chat_id` can in principle be rebound or a user can own multiple chats per domain later, while `UserSettings` is a property of the *person*, not the chat — keeping them as separate aggregates avoids a future schema contortion.
- **`telegram/`** — the *only* folder allowed to import the bot framework SDK. This is what makes "swap Telegram for something else later" actually true rather than aspirational.
- **`persistence/`** — shared DB plumbing (engine, per-user session factory, the shared `bot.db` file, ORM models, migrations) used by every context's `infrastructure/` repository. Centralizing this is what makes both the per-user-file routing *and* the bot.db routing (Step 8) a single, well-tested piece of code instead of duplicated logic per context.
- **`tests/`** mirroring `src/` 1:1 — keeps navigation intuitive ("where are the tests for X" always has one obvious answer).
- **`docs/adr/`** — Architecture Decision Records, one short Markdown file per significant decision (e.g. "0001-sqlite-file-per-chat-context.md"). Given a 3-year maintenance horizon, future-you (or anyone else) needs to know *why* a decision was made, not just what it is.
- **`deployments/`** — keeps container/orchestration config out of application code; supports both the current personal-server (`systemd` unit) and the future containerized/cloud path (`docker-compose.yml`) without one blocking the other.
- **`requirements`/dependency files** — handled via `pyproject.toml` only (see Step 11) rather than a separate `requirements/` folder — flagged as a deliberate deviation from the example skeleton in the prompt, justified in Step 11.
- **`data/`** — gitignored runtime state, kept out of `src/` so the application package stays stateless and image-buildable without bundling user data.

---

## Step 4 — Domain Design

### Entities (with Aggregate Roots marked)

**`Project`** *(Aggregate Root, `projects` context)*
- `id`, `name: ProjectName`, `chat_id: ChatId`, `owner: TelegramUserId`, `created_at`
- Behavior: `rename(new_name: ProjectName)`

**`Task`** *(Aggregate Root, `tasks` context)*
- `id`, `description: ShortDescription`, `status: TaskStatus`, `deadline: Deadline | None`, `project_id: ProjectId`, `chat_id`, `owner`, `completed_at: date | None`
- Behavior: `mark_done(clock)`, `mark_in_progress()`, `reschedule(new_deadline)`, `defer_to(new_date)`
- **Design note:** `Task` references `Project` *by id only*, not as a nested object. Per DDD aggregate-sizing guidance, aggregates should be small — a `Project` with hundreds of nested `Task` objects would force loading all tasks every time the project is touched (e.g. just to rename it).

**`Habit`** *(Aggregate Root, `habits` context)*
- `id`, `name`, `habit_type: HabitType`, `current_streak: Streak`, `longest_streak: Streak`, `chat_id`, `owner`
- Behavior: `check_in(value, effective_date, rollover_policy) -> HabitCheckedInEvent`
- **Design note:** `current_streak`/`longest_streak` are **denormalized onto the aggregate root** deliberately — the Daily Standup hot path needs instant streak display every single day, while the full check-in history is a cold path only needed for `/habit_report`. This is a conscious read-pattern-driven denormalization, not an accident.

**`HabitCheckIn`** *(child record, `habits` context)*
- `id`, `habit_id`, `effective_date`, `value` (bool or numeric), `checked_at`
- Kept in a separate repository from `Habit` rather than nested in the aggregate, for the same hot-path/cold-path reason above.

**`ChatBinding`** *(Aggregate Root, `chat_context` context)*
- `chat_id` (PK), `domain_context: DomainContext`, `bound_by: TelegramUserId`, `bound_at`

**`UserSettings`** *(Aggregate Root, `users` context)*
- `telegram_id: TelegramUserId` (PK), `timezone: Timezone` (default `Asia/Phnom_Penh`, UTC+7), `standup_hour: StandupHour`, `rollover_hour: RolloverHour`, `created_at`
- Behavior: `update_timezone(tz)`, `update_standup_hour(hour)`, `update_rollover_hour(hour)` — plain saves, **no event emitted**. There's nothing to react to: the scheduler's hourly tick (Step 7) re-reads `UserSettings` fresh on every tick, so a changed hour takes effect on the very next tick automatically.
- **Design note:** registered the moment a user runs their first `/init_work` or `/init_habit`, seeded with the UTC+7 default and hour `9` / hour `2`. Granularity is deliberately **hour-of-day only** (no minutes) — this directly enables the single-hourly-tick scheduler design in Step 7, trading minute-level precision for a much simpler scheduling model, appropriate for a non-latency-sensitive personal assistant bot.

**`Quote`** *(plain immutable entity, `quotes` context — not an Aggregate Root in the per-request sense)*
- `id: int`, `sequence_index: int` (0–99 within its `domain_context`), `text: str`, `author: str | None`, `domain_context: DomainContext`
- No behavior — 100 rows per `domain_context` are seeded once into the shared `bot.db` (Step 8) and loaded into memory at process startup; never mutated at runtime.
- **Design note:** 100 quotes per domain was chosen specifically so a simple, deterministic **day-of-year-mod-100** rotation (`GetMotivationalQuoteUseCase`, Step 6) shows a *stable-for-the-day* quote in the Daily Standup without ever repeating inside a single ~100-day cycle, with no "last shown" state to track per user. The same 100-quote pool is also drawn from with a **random** strategy whenever a quote is attached to a one-off action (task completed, habit checked in, report viewed — Step 6) — repeats across separate actions are acceptable here since each is a distinct positive-reinforcement moment, not "today's" quote. If you ever want true no-repeat-per-user tracking instead, that's the seam to revisit — not designed now, since it would require persisting per-user quote history for a purely cosmetic feature.

### Value Objects (immutable, self-validating)
- `ChatId`, `TelegramUserId` — wrap raw Telegram ints, validate positivity.
- `ProjectName` — non-empty, trimmed, max length.
- `ShortDescription` — max length boundary enforced at construction.
- `TaskStatus` — enum-backed VO; centralizes the (currently permissive) transition rule in one place so tightening it later (Step 1, weakness #6) is localized.
- `Deadline` — nullable date wrapper; deliberately allows "no deadline" (Step 1, weakness #4).
- `HabitType` — `BINARY` or `NUMERIC(target: PositiveInt, unit: str)`.
- `Streak` — `current: NonNegativeInt`, with the invariant `longest >= current` enforced on every update.
- `DateRange` — `start`, `end`, `contains(date)` — used by Reporting for "Yesterday / 7 days / 30 days".
- `DomainContext` — `WORK | HABIT` enum.
- `Timezone` — validated IANA tz string (default `Asia/Phnom_Penh`, i.e. UTC+7).
- `StandupHour` / `RolloverHour` — wrap an `int` hour-of-day (0–23), interpreted against the owning user's `Timezone`; deliberately no minute component (see Step 7 for why).

### Domain Services (logic that doesn't belong to a single entity)
- **`RolloverService`** *(tasks)* — given yesterday's unfinished tasks + a reference date, computes the auto-move vs. manual-defer split. Pure function, no I/O.
- **`StreakCalculationService`** *(habits)* — given a `Habit`, its check-in history, the day-rollover boundary, and "effective today", decides whether a streak continues, resets, or increments. **This is the single highest-risk piece of logic in the system** (timezone + late-night-cutover math) and should carry the heaviest unit-test investment in the whole codebase.
- **Reporting aggregation is intentionally *not* a domain service** — it has no invariants to protect, only read-side grouping, so it lives as an application-layer query (CQRS-lite), free to use a leaner, hand-tuned query path instead of full entity reconstruction.

### Repositories (ports in `domain/repository.py`, implementations in `infrastructure/`)
- `ProjectRepository`: `get_by_id`, `list_by_chat`, `save`, `delete`.
- `TaskRepository`: `get_by_id`, `list_by_project`, `list_unfinished_before(chat_id, date)`, `save`, `delete`, `delete_by_project_id` (used by the cascading-delete use case below).
- `HabitRepository` / `HabitCheckInRepository` — kept separate, per the hot/cold path reasoning above.
- `ChatBindingRepository`: `get_by_chat_id`, `save` — backed by the shared `bot.db` (Step 8), not any per-user file.
- `UserSettingsRepository`: `get_by_telegram_id`, `save`, `list_all` — also backed by `bot.db` (`user_schedule` table), not the owner's per-`telegram_id` file. `list_all` is what the scheduler's hourly tick calls (Step 7) to get every user's schedule in one query.
- **No `QuoteRepository`.** `quotes/` deliberately has no per-request repository interface — there's nothing to query by id/filter at runtime beyond "give me quote N for this domain_context," which the `QuoteProvider` (Step 6/7) answers from an in-memory cache loaded from `bot.db` once at startup.

### Aggregates and cross-aggregate consistency
- `Project` and `Task` are **separate aggregates**. The requirement "deleting a project deletes all its tasks" is a cross-aggregate concern, and per DDD guidance that belongs in the **application layer**, not as a domain-model cascade:

  `DeleteProjectUseCase`: confirm precondition → `TaskRepository.delete_by_project_id(id)` → `ProjectRepository.delete(id)`, both wrapped in one `UnitOfWork` transaction for atomicity.

- `Habit` check-ins follow the same pattern: a check-in atomically updates the streak counters and writes the check-in record, wrapped in one `UnitOfWork` transaction — but `HabitCheckIn` is still not *nested inside* the `Habit` aggregate, to keep the hot-path read (standup display) cheap.

---

## Step 5 — Telegram Bot Layer

### Commands
Per the SRD's "minimize typed commands, prefer wizards" philosophy, keep the actual slash-command surface small:
- `/start` — onboarding / main menu (launches inline-keyboard root menu for project/task actions).
- `/init_work`, `/init_habit` — bind the current chat to a domain context.
- `/habit` — create-habit wizard entrypoint.
- `/habit_report` — habit streak summary.
- `/report` — task report menu (Yesterday / 7 days / 30 days).
- `/settings` — view/change timezone, standup hour, and rollover hour (inline 24-hour picker keyboard — hour granularity only, no minutes; defaults to UTC+7 / 9 AM / 2 AM on first use).
- `/quote` — on-demand motivational quote (`Random()` strategy), scoped to the current chat's bound `domain_context` (same resolution path as every other domain command). Now one of five surfaces that show a quote, alongside the Daily Standup, task completion, habit check-in, and `/report`/`/habit_report` — see Step 6.
- `/help`.

Everything else (create/update/delete project or task) is reached via inline buttons under `/start`'s menu, consistent with the "no memorized syntax" UX goal.

### Handlers
Handlers are intentionally **thin**: extract raw Telegram primitives → map to an Application DTO/command → call the relevant use case (resolved via the composition root) → pass the result DTO to a **Presenter** → send the rendered message/keyboard. **Zero business logic in a handler** — that rule is what keeps Telegram replaceable.

### Middleware
- **`chat_context_middleware`** — resolves `chat_id → DomainContext` before the handler runs; blocks domain-specific commands in unbound chats with a setup prompt.
- **`authorization_middleware`** *(addresses Step 1 gap #3)* — restricts mutating commands to the chat's bound owner; everyone else gets a polite refusal.
- **`error_handling_middleware`** — catches typed domain/application exceptions and maps them to friendly replies; unexpected exceptions get logged with a correlation id and a generic apology.
- **`logging_middleware`** — structured log per update: user id, chat id, command/callback, correlation id.

### Conversation flows (wizards)
Implemented via the chosen framework's FSM (e.g. aiogram's `FSMContext`). The FSM owns **only UI state** ("which input am I waiting for next"), never business state. Example — `CreateTaskWizard`: `AWAITING_DESCRIPTION → AWAITING_PROJECT_SELECTION → AWAITING_DEADLINE → CONFIRM → invoke CreateTaskUseCase`.

### Callback query handling
Inline button callbacks encode a compact, structured payload (e.g. `task:complete:<task_id>`), dispatched through a small `CallbackQueryRouter` by prefix, then funneled through the same thin-handler → use case → presenter pattern as commands. Telegram's 64-byte `callback_data` limit is treated as a contract constraint, covered by contract tests (Step 9).

### Error handling strategy (3 layers)
1. Domain/application raise typed exceptions (`ProjectNotFoundError`, `InvalidStatusTransitionError`, `NotAuthorizedError`).
2. `error_handling_middleware` translates known exception types into friendly, often actionable (retry/cancel button) replies.
3. Anything unhandled is caught at the top-level dispatcher, logged with full context, and replies with a generic apology — never a stack trace to the user.

### Why Telegram stays replaceable
Because (a) handlers depend only on Application-layer interfaces, never domain internals or infrastructure directly; (b) `src/lifesync/telegram/` is the *only* place importing the bot SDK; (c) presenters/keyboards encapsulate all framework-specific UI object construction. Swapping `aiogram` for another SDK — or adding a second UI surface (Discord, Slack, a web dashboard) — means writing a new adapter module alongside `telegram/`, with zero changes to domain or application code.

---

## Step 6 — Application Layer

### Use cases (one responsibility each)
- **Projects:** `CreateProjectUseCase`, `RenameProjectUseCase`, `DeleteProjectUseCase` (cascades via UoW, see Step 4), `ListProjectsUseCase`.
- **Tasks:** `CreateTaskUseCase`, `UpdateTaskUseCase`, `DeleteTaskUseCase`, `ListTasksUseCase`, `RolloverUnfinishedTasksUseCase`, `DeferTaskUseCase`.
- **Habits:** `CreateHabitUseCase`, `CheckInHabitUseCase`, `GetHabitReportUseCase`, `ListHabitsForStandupUseCase`.
- **Reporting:** `GenerateTaskReportUseCase(chat_id, range: DateRange)`.
- **Chat Context:** `BindChatContextUseCase`, `ResolveChatContextUseCase`.
- **Users:** `RegisterUserUseCase` (seeds `UserSettings` with UTC+7 / hour-9 / hour-2 defaults on first `/init_*`), `UpdateTimezoneUseCase`, `UpdateStandupHourUseCase`, `UpdateRolloverHourUseCase`, `GetUserSettingsUseCase`. These are plain command handlers — no event needs to be published on change, because the Scheduler (Step 7) never caches a per-user trigger to invalidate; it re-reads `UserSettings` on every hourly tick.
- **Quotes:** `GetMotivationalQuoteUseCase(domain_context, strategy)` — pure function over the in-memory `Quote` list, with two selection strategies:
  - `DailyRotation(today: date)` — `index = today.timetuple().tm_yday % 100`, deterministic, used by the Daily Standup so the quote stays stable all day.
  - `Random()` — uses an injected `RandomProvider` port (new, lives in `shared_kernel/` next to `Clock`) instead of calling `random.choice()` directly, so action-triggered quotes stay deterministic and seedable in tests; used everywhere a quote is a *reaction to a one-off action* rather than "today's" quote (see below).

  Both strategies are pure, no I/O, no repository call.
- **Quote attachment points (beyond the Standup):**
  - `UpdateTaskUseCase` — when the status transition lands on `DONE` (a task is completed), it additionally calls `GetMotivationalQuoteUseCase(WORK, Random())` and attaches the result to the returned `TaskDTO` as `quote: QuoteDTO | None` (populated only on that transition, `None` for every other edit).
  - `CheckInHabitUseCase` — after the atomic check-in + streak update, calls `GetMotivationalQuoteUseCase(HABIT, Random())` and attaches it to the returned check-in DTO, alongside the updated streak count — reinforcing the existing "🔥 N days" positive-reinforcement UX from the SRD.
  - `GenerateTaskReportUseCase` and `GetHabitReportUseCase` — after building the report, each calls `GetMotivationalQuoteUseCase(domain_context, Random())` and attaches it to the report DTO, rendered once below the report content.

  All four are plain synchronous calls from one application use case into `quotes/`'s public use case — the same cross-context composition pattern `GenerateStandupUseCase` already established, not an event. An event was considered (`Habit.check_in()` already had a `HabitCheckedInEvent` reserved) but rejected here: every one of these triggers already produces a direct response to a user-initiated Telegram interaction, so attaching the quote synchronously to that one response is simpler and gives better UX than a delayed, separately-pushed follow-up message.
- **Standup composition:** `GenerateStandupUseCase(chat_id)` — resolves the chat's `domain_context` first, then calls *either* `ListTasksUseCase`/rollover (for `WORK` chats) *or* `ListHabitsForStandupUseCase` (for `HABIT` chats) through their public application interfaces only, plus `GetMotivationalQuoteUseCase(domain_context, DailyRotation(today))` — never reaching into another context's domain or infrastructure directly. This composition module exists so `tasks/`, `habits/`, and `quotes/` stay mutually unaware of each other and of the scheduler.

### Commands vs. Queries (CQRS-lite)
Mutating use cases (`CreateTask`, `CheckInHabit`, …) are **command handlers**; pure-read use cases (`ListTasks`, `GenerateTaskReport`, `GetHabitReport`) are **query handlers**. Query handlers are explicitly permitted to bypass the full repository abstraction in favor of a leaner, hand-tuned query (e.g. one SQL join for a report instead of reconstructing full entities) — a deliberate, documented exception to "always go through the repository," recorded as an ADR.

### DTOs
Plain immutable data classes (or pydantic models) at the Application ↔ Telegram boundary. **Domain entities and ORM models never cross this boundary directly** — this keeps the bot UI insulated from both persistence schema changes and domain refactors, and keeps the DTO shape stable enough to reuse if a REST API is ever added in front of the same application layer.

### Layer responsibilities and boundaries
- **Domain:** invariants, pure logic. Zero I/O, zero framework imports (no SQLAlchemy, no aiogram).
- **Application:** orchestration, transactions (`UnitOfWork`), calling repository/port interfaces, mapping entities ↔ DTOs, publishing domain events. No Telegram types (`InlineKeyboardMarkup` is never imported here), no raw SQL/ORM specifics (those live behind repository interfaces).

---

## Step 7 — Infrastructure Layer

| Concern | Approach | Library |
|---|---|---|
| Database access | Async ORM/Core, explicit entity↔model mapping (no decorators on domain classes) | **SQLAlchemy 2.0 (async)** + `aiosqlite` now, swappable to `asyncpg` later |
| Migrations | Versioned schema changes | **Alembic** |
| External APIs | Reserved `infrastructure/external/` slot behind a port — none needed today beyond Telegram | — |
| Motivational quotes | 200 quotes (100 WORK + 100 HABIT) seeded once into the shared bot database, loaded into memory at startup; see Step 8 | read via the same SQLAlchemy session as the bot db, cached in-process after first load |
| Telegram client | Wrapped behind `notifier_port` so scheduling jobs never import aiogram directly | **aiogram 3.x** |
| Logging | Structured JSON to stdout, correlation id via `contextvars` | `structlog` (or stdlib `logging` + JSON formatter) |
| Configuration | Typed, validated, fail-fast at startup | **pydantic-settings** |
| Cache | Hot-path chat-context lookups; in-memory now, swappable to Redis at multi-instance scale | `cachetools` (in-proc TTL) → Redis later, behind `cache_port` |
| Scheduler | In-process now; **two fixed hourly-tick jobs total** (one for standup, one for rollover), not one job per user — each tick scans all users and fires for whoever's local hour matches their configured `StandupHour`/`RolloverHour`; swappable to managed cron+queue later, behind `scheduler_port` | **APScheduler** (`AsyncIOScheduler`) |
| Secrets | `.env` locally; platform-injected env vars or a secrets manager in production | `python-dotenv` (dev only) |
| DI / composition | Manual wiring in `bootstrap.py` — simplest to debug; introduce `dependency-injector` only if wiring complexity actually grows | — |

**Single hourly-tick scheduling (chosen over one job pair per user):** the scheduler registers exactly **two fixed jobs for the bot's entire lifetime** — `standup_tick` and `rollover_tick` — each an APScheduler `CronTrigger(minute=0)` firing once every hour, in a fixed reference timezone (UTC is fine; conversion to each user's local hour happens inside the job, not in the trigger). Each tick:
1. Runs **one query** against the shared bot database's `user_schedule` table — `SELECT telegram_id, timezone, standup_hour FROM user_schedule` (or `rollover_hour` for the rollover tick) — returning every user's schedule in a single round trip. **No per-user file is opened during this step** (see Step 8 — this is precisely why schedule data was moved out of the per-user files into the shared bot db).
2. For each row, converts "now" into that user's local time.
3. If the local hour matches the user's configured hour, opens that one user's own file (only now, only for the users who actually match this hour) and runs `GenerateStandupUseCase` (or the rollover/streak-finalization use case); everyone else is skipped after step 1's single cheap query — no file I/O for non-matching users at all.

**Why this beats one job pair per user, and why schedule data lives in the bot db, not per-user files:** a settings change via `/settings` is a plain DB write to the bot db — the very next tick picks it up, with **no event bus, no job add/remove/reschedule logic at all**. And because every tick's first step is "who matches this hour," centralizing that lookup table means the scheduler never has to open all N per-user SQLite files just to read a timezone and an hour — it opens exactly one small shared file, then only the files of users who are actually about to receive a message. The trade-off is hour-level precision only (no minutes), already baked into `StandupHour`/`RolloverHour` at the domain level (Step 4) — entirely acceptable for a non-latency-sensitive personal assistant, and both simpler and lighter than either dynamically managing `2 × N` per-user triggers or scanning every user's individual file on every tick.

**Bot framework choice — aiogram over python-telegram-bot:** both are solid; aiogram is chosen for its native async-first design and built-in FSM support that maps directly onto the SRD's wizard/conversation requirement, with active middleware support matching the architecture above.

---

## Step 8 — Database Design

### Partitioning decision: one SQLite file per `telegram_id`, plus one shared **bot database**
Confirmed partition key for domain data: **`telegram_id`**. `data/users/<telegram_id>.db` holds that user's `projects`, `tasks`, `habits`, and `habit_checkins` — both their `WORK` and `HABIT` chats live in the same physical file, distinguished internally by a `chat_id`/`domain_context` column rather than by a separate file per room.

**Refinement (per explicit decision): the bot keeps its own database for everything it needs to check *about* users, rather than opening every user's file.** A single shared file, `data/bot.db`, holds:

```
chat_bindings(chat_id PK, owner_telegram_id, domain_context, bound_at)
user_schedule(telegram_id PK, timezone DEFAULT 'Asia/Phnom_Penh',
              standup_hour INT DEFAULT 9, rollover_hour INT DEFAULT 2, created_at)
quotes(id PK, domain_context, sequence_index INT, text, author NULL)   -- 200 seeded rows, never written at runtime
```

**Why this is the right move, and why it's lighter than the earlier design:** the scheduler's hourly tick (Step 7) needs to ask "whose local hour matches right now?" for *every* user, every hour. Doing that by opening each user's individual file would mean N file-opens per tick just to read a timezone and an hour — wasted I/O that has nothing to do with that user's actual task/habit data. Centralizing `user_schedule` (and `chat_bindings`, which already had to be shared for the chat-routing reason below) into one small file turns that into **one query against one file**, full stop. A per-user file is opened only afterward, only for the users who actually matched this hour and are about to receive a standup/rollover message.

`quotes` belongs here for the same reason: it's content the bot itself owns and serves identically to every user — not user data, so it has no business being duplicated or partitioned per `telegram_id`. Seeded once via a migration/seed script (`scripts/seed_quotes.py`, Step 3), loaded into memory at startup, never written again at runtime.

**The underlying reason a shared file is unavoidable in the first place:** every incoming Telegram update and every scheduler job carries a `chat_id`, but resolving *which user's file to open* and *which domain that chat represents* requires a lookup that can't live inside the very file it's trying to locate — `chat_bindings` has to sit outside any single user's file regardless of how schedule/quotes are organized.

**Routing flow:**
- *Live Telegram update:* `from.id` (the sender) is present on almost every update — usually no `bot.db` lookup is needed to find the *domain* file. `bot.db` is still consulted by `chat_context_middleware` to resolve `chat_id → domain_context` (so the right command set/UI is shown) and, for `authorization_middleware`, to confirm the sender *is* `owner_telegram_id` before allowing a mutating action.
- *Scheduler job (standup/rollover):* one query against `bot.db.user_schedule` per tick (Step 7) to find matching users, then one per-user file open per match, using `chat_bindings` to know which `chat_id` to push to.

A `BotDbRouter`/`UserFileRouter` pair inside `persistence/db.py` is the **only** place that knows `bot.db` and the per-user files are physically separate — it resolves the correct engine/session per repository call. Every repository above it just operates on "a session."

### Risk called out explicitly
SQLite has weak concurrent-writer guarantees across processes. A given user's own scheduler-triggered writes (if any) and their live Telegram updates both write to *the same per-user file* — `database is locked` errors are a real risk under load, though contention is naturally bounded to one user's own activity. `bot.db` itself sees much lighter write traffic (only `/init_*`, `/settings`, and the occasional quote reseed) against frequent reads, so it's the less risky of the two files. Mitigations either way: `PRAGMA journal_mode=WAL`, a short `busy_timeout`, short write transactions. **This remains the documented forcing function to migrate to PostgreSQL** once usage grows beyond personal scale (Step 13) — and because all access goes through repository interfaces, that migration touches only `infrastructure/persistence/`, nothing above it.

### ORM strategy
SQLAlchemy 2.0, explicit mapper classes separate from domain entities — no Active Record, no business logic on ORM models.

### Migrations
Alembic, with **two separate migration histories**: one for the `bot.db` schema (applied once), one for the per-user schema (applied via a startup routine that iterates every known user file, enumerated from `bot.db.chat_bindings`, not a directory scan). The per-user side is the one noted as a scaling concern (N files to migrate) that gets easier, not harder, once Postgres consolidation happens (Step 13) — `bot.db` migrations stay trivially single-file regardless of user count.

### Repository implementation pattern
Interface in `domain/repository.py` (e.g. `class TaskRepository(Protocol): ...`); concrete `SqliteTaskRepository` in `infrastructure/`, constructed with an already-resolved session (file routing happens one layer above, in the Unit-of-Work/session factory — not inside the repository itself). `ChatBindingRepository`, `UserSettingsRepository`, and the quote loader are always wired to the `bot.db` session instead of any individual user session.

### Sample schema sketch

**Per-user file (`data/users/<telegram_id>.db`) — domain data only:**
```
projects(id PK, chat_id, name, created_at, updated_at)
tasks(id PK, chat_id, project_id FK→projects.id, description, status,
      deadline DATE NULL, created_at, updated_at, completed_at NULL)
habits(id PK, chat_id, name, habit_type,
       numeric_target NULL, numeric_unit NULL,
       current_streak INT, longest_streak INT, created_at)
habit_checkins(id PK, habit_id FK, effective_date DATE,
               value, checked_at TIMESTAMP, UNIQUE(habit_id, effective_date))
```
`owner_telegram_id` columns are dropped from `projects`/`tasks`/`habits` — the file itself *is* the owner partition. `chat_id` is kept on each row purely to distinguish `WORK` vs `HABIT` data within the single file. `user_settings` no longer lives here — it moved to `bot.db.user_schedule` above.

**Shared bot database (`data/bot.db`) — everything the bot needs to check about users, in one place:**
```
chat_bindings(chat_id PK, owner_telegram_id, domain_context, bound_at)
user_schedule(telegram_id PK, timezone, standup_hour, rollover_hour, created_at)
quotes(id PK, domain_context, sequence_index, text, author NULL)
```

---

## Step 9 — Testing Strategy

| Layer | What's tested | How |
|---|---|---|
| **Unit** | Entities, value objects, domain services (`StreakCalculationService`, `RolloverService`) | Pure functions, zero mocks. Application use cases tested against hand-rolled **in-memory fake repositories** implementing the same `Protocol` (preferred over mock assertions — more robust to refactors). |
| **Integration** | Real SQLite repositories against a migrated schema | tmp-file or `:memory:` SQLite, real SQLAlchemy session, asserts the router opens the correct per-user file vs. `bot.db` (`ChatBindingRepository`, `UserSettingsRepository`, and the quote loader must hit `bot.db`, never a per-user file). |
| **E2E** | Full update → middleware → handler → use case → DB → outgoing message, for golden paths | aiogram test transport / mocked session simulating real Updates. Covers: create project → create task → mark done → standup reflects it → report reflects it. |
| **Contract** | Telegram Bot API structural constraints (e.g. `callback_data` ≤ 64 bytes, keyboard shape) | Assertion-style tests on payload builders. (Classic schema/Pact-style contract testing becomes relevant only once a second external API, e.g. calendar, is added.) |

**Mocking discipline:** mock only at architectural boundaries — Telegram client, Scheduler, **Clock** (injected everywhere "now" matters; domain/application code never calls `datetime.now()` directly), **RandomProvider** (injected everywhere a quote — or any future randomized choice — is picked; domain/application code never calls `random.choice()` directly). This is what makes `freezegun`-driven tests of the 2 AM rollover boundary, streak-break logic, and a fake-seeded `RandomProvider`-driven test of "task completion attaches quote #N" all fully deterministic. Never mock the domain layer itself.

### Test folder structure (mirrors `src/lifesync/` 1:1)
```
tests/
├── unit/{shared_kernel,projects,tasks,habits,chat_context,users,quotes}/...
├── integration/
│   ├── persistence/  (test_sqlite_*_repository.py, test_bot_db_router.py, test_user_file_router.py)
│   └── scheduling/   (test_apscheduler_adapter.py)
├── e2e/telegram_flows/  (test_project_lifecycle_flow.py, test_daily_standup_flow.py, test_habit_checkin_flow.py,
│                         test_task_completion_quote_flow.py, test_report_quote_flow.py)
├── contract/  (test_telegram_payload_constraints.py)
├── fakes/  (fake_project_repository.py, fake_task_repository.py, fake_clock.py, fake_random_provider.py, fake_notifier.py)
└── conftest.py
```

---

## Step 10 — Configuration & Environment Management

### `.env.example`
```
ENVIRONMENT=local                  # local | dev | staging | production
BOT_TOKEN=
BOT_MODE=polling                   # polling | webhook
LOG_LEVEL=INFO
DATA_DIR=./data
BOT_DB_PATH=./data/bot.db          # shared: chat_bindings, user_schedule, quotes — the bot's own data
USER_DB_DIR=./data/users           # per-telegram_id files: {USER_DB_DIR}/{telegram_id}.db — domain data only
DEFAULT_TIMEZONE=Asia/Phnom_Penh    # UTC+7 — seeded into UserSettings on first /init_*, user-overridable via /settings
DEFAULT_STANDUP_HOUR=9              # seeded default only — per-user from then on, hour-of-day granularity (0-23)
DEFAULT_ROLLOVER_HOUR=2             # seeded default only — per-user from then on, hour-of-day granularity (0-23)
SENTRY_DSN=                        # optional, production error tracking
```
Note: `DEFAULT_*` values here are only the **seed** applied to a brand-new `UserSettings` row at registration. From that point on, each user's actual standup/rollover hour and timezone live in `bot.db`'s `user_schedule` table (Step 8) — not in any per-user file — and are changed via `/settings`, not by editing `.env`.

### Environment separation
A single typed `Settings` class (pydantic-settings) reads `ENVIRONMENT` to drive behavior: `local` uses long-polling + verbose console logs; `staging`/`dev` mirror production code paths against a **separate Telegram bot token** (Telegram allows only one poller/webhook per token — staging cannot share prod's bot); `production` uses webhook mode, JSON logs, and Sentry enabled.

### Secret handling
- `.env` is gitignored; `.env.example` lists keys with placeholders only, never real values.
- Production prefers platform-injected env vars or a secrets manager over files on disk.
- The bot token is treated like a password — rotate via @BotFather immediately if ever leaked.
- CI secrets live in GitHub Actions encrypted secrets, never echoed in logs.

---

## Step 11 — Dependency Management

**Recommendation: `uv` with a single `pyproject.toml` (PEP 621), `src/`-layout.**

**Why `uv` over Poetry or pip-tools:**
- Significantly faster resolver/installer (Rust-based) — meaningfully shortens CI time and local iteration loops on a personal project where every bit of friction tax compounds.
- `uv.lock` plus standards-aligned `pyproject.toml` (no Poetry-specific `[tool.poetry]` dialect) means less vendor lock-in if you ever want to move tooling later.
- Subsumes pip-tools' lockfile-compiling use case while also replacing venv/install tooling — one tool instead of two for a solo maintainer.
- **Trade-off accepted:** uv is newer, smaller ecosystem than Poetry, occasional build-backend rough edges — acceptable given this project's scale; Poetry remains a safe fallback if a real blocker appears.

**Dependency groups in `pyproject.toml`:**
- `[project.dependencies]` — runtime only: `aiogram`, `sqlalchemy`, `alembic`, `pydantic-settings`, `apscheduler`, `structlog`.
- `[dependency-groups.dev]` — `pytest`, `pytest-asyncio`, `freezegun`, `ruff`, `mypy` — never shipped into the production image.

**Versioning:** SemVer, starting `0.x` while pre-stable (signals "expect breaking changes"); promote to `1.0.0` once the SRD's core feature set is feature-complete and in daily personal use. Tag releases in git; maintain `CHANGELOG.md` (Keep a Changelog format) — valuable over a 3-year horizon when you need to trace "when did rollover logic change."

---

## Step 12 — Deployment Architecture

### Docker
Single multi-stage `Dockerfile`: builder stage runs `uv sync --frozen` and builds the app; slim runtime stage copies the venv + code, runs as a **non-root user**. `data/` is a mounted volume — the image itself stays stateless and redeployable without data loss.

### CI/CD (GitHub Actions)
- **`ci.yml`** (every PR/push): lint (`ruff`), type-check (`mypy`), unit + integration tests with coverage, Docker build (no push) to catch build breaks early.
- **`cd.yml`** (on merge to `main`/tag): build + push to a registry (GHCR is the simplest free start), then deploy — for the personal-server phase, an SSH-based `docker compose pull && up -d` step is sufficient. This step is the explicit seam to swap for a cloud target (ECS/Cloud Run/Fly.io) later without touching `ci.yml`.

### Monitoring & alerting (right-sized for personal scale)
- Structured JSON logs to stdout, captured by Docker's logging driver.
- **Sentry** (free tier) wired into the global exception handler for error tracking — cheap, immediate value.
- A periodic **heartbeat job** that pings the maintainer's own Telegram chat if the scheduler hasn't run in N hours — a cheap dead-man's-switch, deferring full Prometheus/Grafana/Alertmanager until traffic actually justifies that ops overhead. The ports-based scheduler design means adding real metrics later (`prometheus-client` on an internal port) is additive, not a rewrite.

### Logging strategy
One structured line per inbound update (correlation id, chat/user id, command, latency, outcome) and one per background job run (job name, duration, outcome, counts) — enough to answer "did the 9am standup fire for chat X" without a dashboard.

### Health checks
A minimal internal `/healthz` endpoint (tiny `starlette`/`aiohttp` app, or reused if webhook mode's HTTP server is already running) reporting DB reachability, scheduler liveness, and last successful Telegram API call — wired to Docker `HEALTHCHECK` now and to cloud-platform readiness/liveness probes later.

### Polling vs. webhook
**Long-polling for the personal-server phase** — no public HTTPS/cert management needed. The bot composition root abstracts this behind one config flag (`BOT_MODE=polling|webhook`) so flipping to webhook mode for cloud deployment later is a config change, since aiogram's `Dispatcher` supports both identically.

---

## Step 13 — Scalability Review

### Where bottlenecks will appear, in order
1. **SQLite write contention on per-user files** (a given user's own writes only — no cross-user contention by design) — the first real ceiling, though already lighter than earlier drafts since the scheduler's hourly tick no longer touches per-user files for non-matching users (Step 7/8). WAL mode + short transactions buy time; PostgreSQL migration (Step 8) is the real fix, isolated to `infrastructure/persistence/`.
2. **`bot.db` becoming a hot single file** once user count grows — every hourly tick reads it, every `/init_*`/`/settings` writes it. Still just one small file with mostly-read traffic, so this is a much later concern than per-user contention; same WAL/Postgres mitigation path applies.
3. **In-process APScheduler** — fine for one replica; two replicas would double-fire jobs. Fix: keep scheduling pinned to exactly one replica, or externalize to managed cron + queue once horizontal scaling is needed.
4. **Long-polling** — inherently single-process; the concrete trigger to migrate to webhook mode (any replica behind a load balancer can receive the webhook POST).
5. **In-memory chat-context cache** — fine single-instance; becomes Redis-backed (already designed behind `cache_port`) the moment there's more than one process.

### Why this architecture absorbs all of these without a rewrite
Every one of these dependencies (DB, scheduler, notifier, cache, clock) sits behind a port defined in the application layer. Each bottleneck's fix is therefore an **infrastructure-layer swap**, never a domain or Telegram-handler change — that isolation is the entire payoff of the Hexagonal/Clean Architecture investment made in Step 2.

### Migration path: personal project → production system
| Phase | Scale | Storage | Bot mode | Scheduler | Deployment |
|---|---|---|---|---|---|
| 1 (now) | 1 user, 2 chats | SQLite (`bot.db` + per-`telegram_id` files) | Long-polling | In-process APScheduler, 2 fixed hourly ticks | Single Docker container, personal server |
| 2 | dozens of chats, small friend group | Single shared PostgreSQL, `chat_id`-filtered (`bot.db` tables become regular tables in the same instance) | Webhook behind reverse proxy + TLS | In-process, single replica | Single replica, managed TLS |
| 3 | broader/production | Postgres + Redis cache | Webhook, multiple stateless replicas | Externalized cron + queue | Load balancer, Prometheus/Grafana, cloud secrets manager |

None of these phase transitions require rewriting domain or application code — confirmation that the modular monolith + ports design is the right call for a 3-year horizon that starts tiny.

---

## Step 14 — Final Recommendation

### Architecture diagram

```
                              ┌─────────────────────────────┐
                              │        Telegram Cloud        │
                              └───────────────┬──────────────┘
                                  long-poll / webhook
                                              │
┌─────────────────────────────────────────────▼────────────────────────────────────────────┐
│                              TELEGRAM ADAPTER  (driving adapter)                          │
│  Middleware (chat-context, auth, logging, errors) → Handlers → FSM Wizards → Presenters   │
└───────────────────────────────────┬────────────────────────────────────────────────────────┘
                                     │  Application DTOs / Commands / Queries ONLY
┌────────────────────────────────────▼───────────────────────────────────────────────────────┐
│                                  APPLICATION LAYER                                         │
│   Use Cases (Commands & Queries) · Unit of Work · DTO mapping · Domain Event publishing    │
└──────┬───────────────┬───────────────┬───────────────┬───────────────┬─────────────────────┘
       │               │               │               │               │
┌──────▼─────┐┌──────▼─────┐┌──────▼─────┐┌──────▼──────┐┌──────▼───────┐┌──────▼─────┐┌──────▼─────┐
│  Projects  ││   Tasks    ││   Habits   ││  Reporting  ││ Chat Context ││   Users    ││   Quotes   │ DOMAIN
│  (domain)  ││  (domain)  ││  (domain)  ││  (queries)  ││   (domain)   ││  (domain)  ││  (domain)  │ LAYER
└──────┬─────┘└──────┬─────┘└──────┬─────┘└──────┬──────┘└──────┬───────┘└──────┬─────┘└──────┬─────┘ (pure
       │             │             │              │              │              │             │     Python,
       └─────────────┴──────┬──────┴──────────────┴──────────────┴──────────────┴─────────────┘     no I/O)
                             │  Repository / Port interfaces (defined IN domain)
┌────────────────────────────▼───────────────────────────────────────────────────────────────────┐
│                          INFRASTRUCTURE LAYER  (driven adapters)                               │
│  SQLite/SQLAlchemy Repos · BotDbRouter + UserFileRouter (bot.db + per-telegram_id files) ·      │
│  APScheduler Adapter (2 fixed hourly ticks, single bot.db query first) · Telegram Notifier ·    │
│  In-memory/Redis Cache · pydantic-settings Config · structlog Logging                          │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Final folder structure
See Step 3 in full — condensed: `src/lifesync/{shared_kernel, projects, tasks, habits, reporting, chat_context, users, quotes, standup, scheduling, notifications, telegram, persistence}/`, each context split into `domain/ → application/ → infrastructure/`.

### Recommended libraries
`aiogram` · `SQLAlchemy 2.0 (async)` · `Alembic` · `pydantic` / `pydantic-settings` · `APScheduler` · `structlog` · `uv` · `pytest` + `pytest-asyncio` + `freezegun` + `ruff` + `mypy`.

### Key design decisions (recap)
1. **Modular Monolith + Hexagonal/Clean Architecture + lite-DDD** — right-sized for a solo maintainer with a 3-year horizon and genuine future-extraction ambitions.
2. **Telegram confined to one adapter package** — the explicit mechanism satisfying the SRD's "business logic separated from Telegram" requirement.
3. **Ports around DB, Scheduler, Notifier, Cache, Clock** — turns every Step 13 bottleneck into an isolated, additive infrastructure swap.
4. **One SQLite file per `telegram_id` for domain data, plus a shared `bot.db` for everything the bot needs to check about users** (`chat_bindings`, `user_schedule`, `quotes`) — confirmed partitioning. The split exists because `chat_id → owner/domain` must be resolvable before a user's own file can even be located, and because the scheduler needs to ask "who matches this hour?" for every user without opening N individual files just to answer that. PostgreSQL is the explicit next step at scale.
5. **Denormalized streak counters on `Habit`** — a deliberate hot-path/cold-path trade-off, not an oversight.
6. **`Clock` port everywhere "now" matters** — the single change that makes the trickiest logic (day-rollover, streaks) deterministically testable.
7. **CQRS-lite for Reporting** — reads don't need domain invariants, so they're allowed to skip the repository abstraction for performance.
8. **Per-user configurable standup/rollover hour and timezone** (default UTC+7), modeled as a `UserSettings` aggregate with its own bounded context — **deliberately hour-granularity only**, so the scheduler can stay as two fixed hourly-tick jobs that re-read settings every tick, instead of one dynamically managed job pair per user. Chosen as the lighter option: no event-driven reschedule machinery, no per-user job bookkeeping, at the cost of minute-level precision the SRD never asked for.
9. **100 motivational quotes per domain (WORK/HABIT), seeded into `bot.db`, not per user** — content the bot owns and serves identically to everyone, surfaced at five points: the Daily Standup (deterministic `DailyRotation`, stable all day), task completion, habit check-in, `/report`/`/habit_report`, and the on-demand `/quote` command (all four via a `Random` strategy). Both strategies are pure functions over an in-memory list — no "last shown" state to track, and a new `RandomProvider` port (next to `Clock`) keeps the random path just as deterministically testable as the date-based one.

### Potential risks
- **Over-engineering for a one-person project** — mitigated by scoping ports strictly to the six boundaries listed in Step 2, not every dependency.
- **SQLite concurrency under real usage** — mitigated short-term (WAL mode), with an explicit, designed migration path to Postgres.
- **Timezone/owner-authorization gaps in the original SRD** — addressed proactively in the domain model (Step 1) rather than retrofitted later.
- **Solo-maintainer bus factor** — mitigated by ADRs in `docs/adr/` and this document itself, so context survives gaps in active development.

### Maintenance guidelines
- New features start as a new bounded context folder, not as additions inside an existing one, unless they're genuinely the same domain concept.
- Any new external dependency (a calendar API, an LLM call) gets a port in `application/`, never a direct import in domain or handlers.
- Every business-rule change to rollover or streak logic gets an ADR entry — these two areas are the project's highest-complexity, highest-regression-risk surface.
- Keep `shared_kernel/` small; if it starts holding business logic, that logic belongs in a real bounded context instead.
