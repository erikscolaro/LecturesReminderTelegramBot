import arrow  # Imports the 'arrow' library for date and time handling
import schedule  # Imports the 'schedule' library for job scheduling
import telebot  # Imports the 'telebot' library to interact with the Telegram Bot API
import threading  # Imports the 'threading' module for running tasks in parallel
import time  # Provides time-related functions like sleep
from ics import Calendar  # Imports the 'Calendar' class to parse iCal files
from requests import get  # Imports the 'get' function for making HTTP GET requests
import json  # Imports the 'json' module for reading and writing JSON files

# Reads the bot configuration from JSON
def setup():
    with open("conf.json", "r", encoding="utf-8") as file:
        return json.load(file)

CONFIG = setup()  # Loads the configuration into CONFIG
bot = telebot.TeleBot(CONFIG["TOKEN"])  # Initializes the bot with the provided token

# Keeps the bot polling continuously to receive messages
def polling_linker_manager(interval, timeout):
    while True:
        try:
            bot.polling(none_stop=True, interval=interval, timeout=timeout)
        except Exception as e:
            print(e)
            time.sleep(1)

# Sends a reminder (message_text) to a specific channel channel_name
def send_reminder(channel_name, message_text):
    if channel_name in class_info.keys():
        print(f"executing event {channel_name}.")
        bot.send_message(chat_id=class_info[channel_name]["channel_id"], text=message_text)
    return schedule.CancelJob  # Cancels the scheduled job after execution

# Fetches calendar events from the URL in CONFIG,
# checks if they are due to start soon, and schedules reminders
def update_events():
    print(f"Updating events, {arrow.utcnow().to('local')}")
    temporary = arrow.utcnow().floor('hour')
    for e in Calendar(get(CONFIG["URL_ICAL"]).text).events:
        temp_dict = e.__dict__
        print(temp_dict)
        # Schedules a reminder if the event begins within the next hour
        if temporary.shift(hours=1) <= arrow.get(temp_dict['_begin']) < arrow.utcnow().shift(hours=2):
            schedule.every().day.at(
                temp_dict['_begin'].to('local').shift(minutes=-CONFIG["CLASS_REMINDER_MINUTES"]).floor(
                    "minutes").format("HH:mm")
            ).do(
                send_reminder,
                channel_name=temp_dict['name'],
                message_text=temp_dict['description']
            )
    print(schedule.get_jobs())

# Builds inline buttons to display in the bot's response
def create_buttons():
    buttons = telebot.types.InlineKeyboardMarkup()
    for key, value in class_info.items():
        buttons.add(
            telebot.types.InlineKeyboardButton(
                text=key,
                url=value["invite_link"]
            )
        )
    return buttons

# Responds to /classes command: shows the available class buttons
@bot.message_handler(commands=['classes'], chat_types=["private"])
def show_buttons(message):
    bot.send_message(
        chat_id=message.chat.id,
        text=CONFIG["BUTTONS_DESC"],
        reply_markup=create_buttons(),
        parse_mode='HTML'
    )

# Responds to /start command: sends a welcome message and shows buttons
@bot.message_handler(commands=['start'], chat_types="private")
def show_welcome(message):
    bot.send_message(
        chat_id=message.chat.id,
        text=CONFIG["WELCOME"]
    )
    show_buttons(message=message)

# Responds to /info command: sends an info message
@bot.message_handler(commands=['info'], chat_types="private")
def show_info(message):
    bot.send_message(
        chat_id=message.chat.id,
        text=CONFIG["INFO"]
    )

# Responds to /admin command: checks the password and shows admin options
@bot.message_handler(commands=['admin'], chat_types="private")
def admin_commands(message):
    delete_message(message)
    if CONFIG["PASSWORD"] in message.text:
        control_panel = bot.send_message(
            chat_id=message.chat.id,
            text="***Admin control panel commands***\n"
                 "To change the password:\n"
                 "/admin_password <old password> <new password>"
        )
        time.sleep(10)
        delete_message(control_panel)
    else:
        err_msg = bot.send_message(chat_id=message.chat.id, text="Wrong password!")
        time.sleep(2)
        delete_message(err_msg)

# Responds to /admin_password command: changes the bot's password
@bot.message_handler(commands=['admin_password'], chat_types="private")
def change_password(message):
    if CONFIG["PASSWORD"] in message.text:
        CONFIG["PASSWORD"] = message.text.split(sep=" ")[2]
        print(CONFIG["PASSWORD"])
        setup(save_changes=True)  # Imagined parameter to indicate saving changes
        conf_msg = bot.send_message(chat_id=message.chat.id, text="Password changed successfully.")
        time.sleep(2)
        delete_message(conf_msg)
    else:
        err_msg = bot.send_message(chat_id=message.chat.id, text="Wrong password!")
        time.sleep(2)
        delete_message(err_msg)
    delete_message(message)

# Deletes a user message by ID (used inside admin functions)
@bot.message_handler(func=lambda message: True, chat_types="private")
def delete_message(message):
    print(message.text)
    bot.delete_message(message.chat.id, message.message_id)

# Handles /register or /delete commands within a channel to add or remove channel info
@bot.channel_post_handler(commands=['register', 'delete'])
def manage_channel(message):
    bot.delete_message(message.chat.id, message.message_id)
    if CONFIG["PASSWORD"] in message.text:
        if '/register' in message.text:
            class_info[message.chat.title] = {
                "invite_link": bot.export_chat_invite_link(message.chat.id),
                "channel_id": message.chat.id
            }
            confirmation_msg = bot.send_message(chat_id=message.chat.id,
                                                text="The channel has been registered.",
                                                disable_notification=True)
            time.sleep(5)
            bot.delete_message(confirmation_msg.chat.id, confirmation_msg.message_id)
        elif '/delete' in message.text:
            class_info.pop(message.chat.title)
            confirmation_msg = bot.send_message(chat_id=message.chat.id,
                                                text="The channel has been deleted.",
                                                disable_notification=True)
            time.sleep(5)
            bot.delete_message(confirmation_msg.chat.id, confirmation_msg.message_id)
    else:
        confirmation_msg = bot.send_message(chat_id=message.chat.id, text="Wrong password.", disable_notification=True)
        time.sleep(5)
        bot.delete_message(confirmation_msg.chat.id, confirmation_msg.message_id)

# Main entry point
if __name__ == '__main__':
    class_info = dict()  # Stores channel data, keyed by channel name {'name': {'invite_link': '', 'channel_id': ''}}
    bot.set_my_commands([
        telebot.types.BotCommand("/classes", "send linker buttons"),
        telebot.types.BotCommand("/info", "send information")
    ])
    # Starts a separate thread to handle bot polling
    threading.Thread(
        target=polling_linker_manager,
        args=(CONFIG["LINKER_REFRESH_INTERVAL"], CONFIG["LINKER_TIMEOUT"],),
        daemon=False
    ).start()
    # Schedules the update_events function to run every hour
    schedule.every().hour.at(":00").do(update_events)
    # Runs scheduled tasks as long as the script is active
    while True:
        schedule.run_pending()
        time.sleep(CONFIG["REMINDER_REFRESH_INTERVAL"])
