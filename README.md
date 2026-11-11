# RasadBot — School Feedback & Communication Bot

**RasadBot** is a Telegram-based feedback management system designed to simplify communication between school administrators and their community, including parents, students, and teachers.

It provides a straightforward way to collect suggestions, concerns, and feedback, organize incoming messages, and respond directly to the sender—all within Telegram. The goal is to make school communication more accessible, structured, and responsive without requiring a separate website or mobile application.

## Features

### For parents, students, and teachers

- **Guided feedback submission:** A step-by-step conversation collects the sender's name, grade level, and message.
- **Optional personal details:** Name and grade level can be skipped; the feedback message is required.
- **Submission confirmation:** Users receive an acknowledgment when their feedback is saved.
- **Direct responses:** Administrators can reply to a submitted message through the bot.
- **Persian-language interface:** The current interaction flow and messages are written in Persian.

### For school administrators

- **Telegram administration panel:** Access management tools using `/admin`.
- **Feedback inbox:** Browse all submissions or filter for unanswered messages.
- **Reply workflow:** Respond to a selected submission from a private chat with the bot.
- **Notifications:** Receive new submissions in configured administrator chats and, optionally, a Telegram group.
- **Statistics:** View total submissions, today's submissions, answered items, and unanswered items.
- **CSV export:** Export feedback records for analysis in spreadsheet applications such as Microsoft Excel.
- **Jalali timestamps:** Display submission dates and times using the Persian calendar.

## How It Works

1. A community member starts the bot with `/start`.
2. The bot asks for an optional name and grade level.
3. The member submits a written suggestion, concern, or feedback message.
4. The submission is stored in a local SQLite database.
5. The sender receives confirmation; configured administrators and the optional group are notified.
6. An authorized administrator selects **Reply**, enters a response in the bot's private chat, and the bot forwards it to the original sender.

## Technology Stack

| Component | Technology |
| --- | --- |
| Programming language | Python |
| Telegram integration | `python-telegram-bot` |
| Data storage | SQLite |
| Configuration | `python-dotenv` and environment variables |
| Persian calendar | `jdatetime` |
| Bot update delivery | Telegram long polling |

## Project Structure

```text
rasad-bot/
├── bot.py             # Main application and bot handlers
├── requirements.txt   # Python dependencies
├── .env.example       # Example environment configuration
├── .gitignore         # Excludes secrets and local runtime data
└── README.md          # Project documentation
```

The application also creates local runtime files such as `rasad.db` and `bot.log`. These should remain outside version control. Other optional scripts may exist in a particular deployment.

## Getting Started

### Prerequisites

- Python and pip installed
- A Telegram bot created through [@BotFather](https://t.me/BotFather)
- Telegram user IDs for the administrators who should have management access

### 1. Clone the repository

```powershell
git clone https://github.com/mortezarezaei1373/rasad-bot.git
cd rasad-bot
```

### 2. Create a virtual environment

On Windows (PowerShell):

```powershell
python -m venv venv
```

### 3. Install dependencies

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure environment variables

If `.env.example` is included, create your local `.env` file from it:

```powershell
Copy-Item .env.example .env
```

Set the following values in `.env`:

```dotenv
BOT_TOKEN=replace_with_your_telegram_bot_token
ADMIN_ID=123456789,987654321
GROUP_ID=-1001234567890
```

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | Yes | Telegram Bot API token obtained from BotFather |
| `ADMIN_ID` | Yes for administration | Comma-separated Telegram user IDs authorized to use admin functions |
| `GROUP_ID` | No | Telegram group chat ID for additional submission notifications |

If group notifications are not needed, omit `GROUP_ID` or leave it empty.

**Never commit a real bot token, user database, logs, or other sensitive deployment data.**

### 5. Run the bot

```powershell
.\venv\Scripts\python.exe bot.py
```

Open the bot in Telegram and send `/start` to try the feedback flow. Authorized administrators can use `/admin` in a private chat with the bot.

## Bot Commands

| Command | Available to | Purpose |
| --- | --- | --- |
| `/start` | Users | Begin a new feedback submission |
| `/cancel` | Users | Cancel an in-progress interaction |
| `/admin` | Configured administrators | Open the Telegram administration panel |

## Data & Privacy

RasadBot stores feedback text, optional submitted name and grade, submission time, Telegram user ID, username, and reply status in a local SQLite database. **Skipping the optional name field does not make a submission technically anonymous:** Telegram identifiers are still stored to support replies.

The administrator panel is restricted using configured Telegram user IDs. Deployments should additionally protect server access, database files, backups, and exported CSV files, and inform users how their feedback is handled.

When deploying a public-facing bot, review applicable privacy and data-retention requirements, especially when collecting messages from students or parents.

## Security Notes

- Keep `.env`, `rasad.db`, `*.log`, virtual environments, and feedback exports out of Git.
- If a bot token is exposed, revoke it with [@BotFather](https://t.me/BotFather), update `BOT_TOKEN` in `.env`, and restart the application.
- Do not publish actual administrator IDs, student information, feedback messages, or production database snapshots.
- Consider reviewing Git history for accidentally committed secrets; adding `.gitignore` later does not erase earlier commits.

## Deployment Notes

RasadBot runs using long polling and can be hosted on a Windows VPS. For continuous operation, it may be started by Windows Task Scheduler or another process manager. Ensure the process starts with the project directory as its working directory so relative files (including the SQLite database and logs) are stored in the intended location.

## Current Scope & Future Improvements

The current implementation focuses on Telegram-based feedback collection and administrator responses. Potential future enhancements include feedback categories, status tracking, advanced reporting, database backup and migration tools, and improved operational monitoring.

## About the Project

RasadBot was developed to bridge the communication gap between school management and the broader school community. By turning feedback into a simple, trackable Telegram conversation, it helps administrators receive input and respond more efficiently while giving parents, students, and teachers an accessible channel to make their voices heard.
