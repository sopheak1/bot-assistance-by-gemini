# System Requirement Document (SRD): Task & Project Management Telegram Bot

## 1. Introduction
This document outlines the system requirements and user experience guidelines for a Telegram-based task and project management bot. The bot acts as a proactive personal assistant, allowing users to manage projects, track tasks, and monitor progress efficiently through an interactive interface.

## 2. Architecture & Scope
- **Audience:** Multi-user support.
- **Context-Aware Group Chats (The "Two Rooms" Approach):** To isolate work stress from personal habits while maintaining a single codebase, the bot operates within **Telegram Group Chats** rather than Direct Messages (DMs). A user creates two separate groups (e.g., "My Work" and "My Habits") and adds the single bot to both. The bot assigns a specific domain context (Task vs. Habit) to each group.
- **Data Isolation:** Data is strictly isolated by `chat_id` (representing the domain context) and the user's Telegram ID. This ensures maximum privacy, fast retrieval, and psychological separation of concerns.

## 3. User Experience (UX) Philosophy
- **Interactive UI Wizard:** To minimize typing errors and friction on mobile devices, the bot utilizes step-by-step prompts and Inline Keyboards. Users do not need to memorize or type complex slash commands with strict syntax.
- **Proactive Assistance:** The bot pushes notifications to help the user plan their day, reducing cognitive load.
- **Simplicity First:** Status workflows and reporting are kept minimal and highly actionable.

## 4. Core Entities
- **Project:** 
  - Attributes: Project Name
- **Task:** 
  - Attributes: Short Description, Status, Deadline, Project ID
- **Habit / Routine:** 
  - Attributes: Name, Habit Type (Binary vs. Numeric Target), Current Streak, Longest Streak
- **Status Enum:** 
  - Allowed states: `To Do`, `In Progress`, `Done`

## 5. Functional Requirements

### 5.1 Project Management
- **Create Project:** A step-by-step prompt asking for the project name.
- **Update Project:** Ability to rename an existing project via inline options.
- **Delete Project:** **Requires mandatory confirmation** via inline buttons (e.g., "Are you sure you want to delete Project X and all its tasks? [Yes, Delete] [Cancel]") to prevent accidental data loss.
- **List Projects:** Displays a summarized view of all active projects.

### 5.2 Task Management
- **Create Task:** Prompts the user for the task description, lets them select the parent project via inline buttons, and sets a deadline. The default status is `To Do`.
- **Update Task:** Allows editing of the description, deadline, and status through interactive buttons.
- **Delete Task:** **Requires mandatory confirmation** via inline buttons.
- **List Tasks:** Displays tasks filtered by project, complete with their current status and deadline.

### 5.3 Daily Planning & Workflow (Proactive Feature)
- **Daily Standup:** Every morning at a configurable time (e.g., 9:00 AM), the bot automatically sends a routine message to the user.
- **Rollover Prompt:** The bot lists all unfinished tasks from yesterday.
- **Actionable Planning:** The user is presented with inline buttons to:
  - Select/Set the to-do list for the current day.
  - Automatically "Move unfinished tickets to today".
  - Manually defer specific tickets to a future date.

### 5.4 Reporting & Progress Tracking
- **Quick Reports:** A `/report` command triggers an inline menu offering time-bound summaries:
  - `[Yesterday]`
  - `[Last 7 Days]`
  - `[Last 30 Days]`
- **Report Output:** Selecting an option returns a concise summary of all tasks that had their progress updated (e.g., moved to `Done` or `In Progress`) within the chosen timeframe, grouped by project and status.

### 5.5 Daily Routine & Habit Tracking
- **Create Habit:** A command (e.g., `/habit`) to create recurring daily routines. Users can choose between **Binary (Yes/No)** (e.g., "Go to bed by 11 PM") or **Numeric** tracking (e.g., "Drink 2L of water").
- **Global Day Rollover:** All habits are expected daily. The system uses a configurable "Day Rollover Time" (e.g., 2:00 AM) so late-night completions count towards the correct day and do not break streaks.
- **Daily Check-in & UI:** Habits are integrated directly into the Daily Standup message. Current streaks are displayed right next to the habit buttons (e.g., `[ ] Sleep by 11 PM (🔥 29 days)`), leveraging positive reinforcement.
- **Streak Reporting:** A `/habit_report` command generates a full summary of all daily tracking and longest streaks.

## 6. Technical Considerations
- **Platform:** Telegram Bot API (using webhooks or long-polling).
- **Storage:** Local file system storing individual SQLite `.db` files in a dedicated `data/` directory.
- **Routing Middleware:** The bot requires strict routing logic to identify the context based on `chat_id`. A setup command (e.g., `/init_work` or `/init_habit`) binds a group chat to a specific domain, ensuring work schedules don't bleed into habit schedules.
- **Interface Components:** High reliance on Telegram's `InlineKeyboardMarkup`, `ReplyKeyboardMarkup`, and `CallbackQuery` handling to deliver the UI Wizard experience.
