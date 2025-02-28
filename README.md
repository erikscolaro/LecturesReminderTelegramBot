# Project Overview
This project hosts a Telegram bot that schedules reminders based on an iCal feed. It uses Python libraries such as Arrow, Schedule, and PyTelegramBotAPI to handle dates, schedule tasks, and interact with the Telegram Bot API.

The core functionality is implemented in `main.py`, which serves as the entry point for the bot. This file:
- Initializes the Telegram bot using credentials from environment variables
- Parses the iCal feed from a configured URL to extract class schedules
- Sets up a scheduling system that periodically checks for upcoming classes
- Sends notifications to registered channels when classes are about to start
- Implements command handlers for user interactions
- Manages persistence of registered channels using a JSON file
- Runs an infinite loop that keeps the scheduler active and processes incoming messages

## Available Commands
- `/start` - Initializes the bot and displays a welcome message with available features
- `/classes` - Shows available class links from the configured schedule
- `/register [password]` - Registers a channel for receiving scheduled notifications (requires admin password)
- `/delete [password]` - Removes a channel from the notification list (requires admin password)
- `/info` - Displays information about the bot and its capabilities
- `/help` - Shows a list of all available commands with brief descriptions
- `/next` - Shows the next scheduled class from the calendar
- `/today` - Displays all classes scheduled for today
- `/tomorrow` - Displays all classes scheduled for tomorrow
- `/week` - Shows the complete schedule for the current week
