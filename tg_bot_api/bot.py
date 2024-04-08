import os
import json
import requests

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)


TOKEN = os.environ["TOKEN"]
BACKEND_URL = os.environ["BACKEND_URL"]

PROMPT_ACTION, \
PROMPT_URGENCY, \
PROMPT_IMPACT, \
CREATE_INCIDENT, \
VIEW_INCIDENT, \
PROMPT_INCIDENT_ACTION, \
PROMPT_CHANGE_STATUS, \
PROMPT_INCIDENT_COMMENT = range(8)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the start command from the user, initiates the conversation.

    Args:
    update (Update): The incoming update from Telegram.
    context (ContextTypes.DEFAULT_TYPE): The context of the conversation.

    Returns:
    int: The next conversation state.

    Raises:
    TelegramError: If failed to communicate with the backend.
    """
    user = update.message.from_user

    def get_user_info(user):
        user_info = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'telegram_user_id': user.id
        }
        if user_info["username"] is None:
            user_info["username"] = user_info["first_name"]
        return user_info

    user_data = get_user_info(user)

    r = requests.post(BACKEND_URL + '/users', data=json.dumps(user_data), verify=False)

    print(r.status_code, r.text)
    if r.status_code not in (200, 201,):
        await update.message.reply_text(f"Oops {user.first_name}, your status code is {r.status_code}")
        return ConversationHandler.END

    text = json.loads(r.text)
    context.user_data["reported_by"] = text[0]["id"]

    reply_keyboard = [
        [InlineKeyboardButton("Create Incident", callback_data="Crt_Inc_Bttn")],
        [InlineKeyboardButton("View Incidents", callback_data="Vw_Inc_Bttn")]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await update.message.reply_text(f"Hi {user.first_name}! Choose your action:", reply_markup=reply_markup)
    return PROMPT_ACTION


async def prompt_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompts the user to select an action: create an incident or view existing incidents.

    Returns:
    int: The next conversation state or ConversationHandler.END to end the conversation.
    """
    message = update.message.text
    if message == "Create Incident":
        await update.message.reply_text("Please, describe your issue:")
        return CREATE_INCIDENT
    elif message == "View Incidents":
        await update.message.reply_text("You don't have any incidents")
        return VIEW_INCIDENT
    else:
        return ConversationHandler.END


async def create_incident_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to create a new incident.

    Returns:
    int: The next conversation state.
    """
    query = update.callback_query
    await query.edit_message_text("Please, describe your issue:", reply_markup=InlineKeyboardMarkup([]))
    return CREATE_INCIDENT


async def view_incidents_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to view existing incidents.

    Returns:
    int: The next conversation state.
    """
    r = requests.get(BACKEND_URL + '/incidents', params={'reported_by': context.user_data["reported_by"]}, verify=False)
    if r.status_code not in (200,):
        await update.callback_query.edit_message_text(f"Your status code is {r.status_code}")

    text = json.loads(r.text)
    context.user_data['incidents'] = text
    reply_keyboard = []
    for incident in text:
        reply_keyboard.append([InlineKeyboardButton(f"{incident['description']}", callback_data=incident['id'])])

    query = update.callback_query

    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await query.edit_message_text("Here's list of your incidents. ", reply_markup=reply_markup)
    return VIEW_INCIDENT


priority_keyboard = [
    [InlineKeyboardButton("High", callback_data="lev_1")],
    [InlineKeyboardButton("Medium", callback_data="lev_2")],
    [InlineKeyboardButton("Low", callback_data="lev_3")]
]

keys = {
    "lev_1": "High",
    "lev_2": "Medium",
    "lev_3": "Low"
}


async def prompt_incident_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompts the user to describe the incident.

    Returns:
    int: The next conversation state.
    """
    message = update.message.text
    context.user_data["description"] = message

    reply_markup = InlineKeyboardMarkup(priority_keyboard)
    await update.message.reply_text(
        f"Incident created with description: {message}.\nPlease, select impact level:", \
                                reply_markup=reply_markup
    )
    return PROMPT_IMPACT


async def set_impact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to set the impact level of the incident.

    Returns:
    int: The next conversation state.
    """
    query = update.callback_query

    context.user_data["impact"] = keys[update.callback_query.data]

    reply_markup = InlineKeyboardMarkup(priority_keyboard)
    await query.edit_message_text(
        f"Impact level set as {keys[update.callback_query.data]}.\nPlease, select urgency level:", \
                                reply_markup=reply_markup
    )
    return PROMPT_URGENCY


async def set_urgency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to set the urgency level of the incident.

    Returns:
    int: The next conversation state or ConversationHandler.END to end the conversation.
    """
    query = update.callback_query

    context.user_data["urgency"] = keys[update.callback_query.data]
    r = requests.post(BACKEND_URL + '/incidents', data=json.dumps(context.user_data), verify=False)

    if r.status_code != 201:
        await query.edit_message_text(f"Oops! Your status code is {r.status_code}")
        return ConversationHandler.END

    text = json.loads(r.text)

    reply_keyboard = [
        [InlineKeyboardButton("Create Incident", callback_data="Crt_Inc_Bttn")],
        [InlineKeyboardButton("View Incidents", callback_data="Vw_Inc_Bttn")]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await query.edit_message_text(
        f"Urgency level set as {keys[update.callback_query.data]}.\nIncident ID: {text[0]['id']}\nChoose action", \
                                reply_markup=reply_markup
    )
    return PROMPT_ACTION


async def view_incident(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to view details of a specific incident.

    Returns:
    int: The next conversation state.
    """
    query = update.callback_query
    inc_id = query.data
    r = requests.get(BACKEND_URL + f'/views/{inc_id}', verify=False)
    if r.status_code not in (200,):
        await update.callback_query.edit_message_text(f"Your status code is {r.status_code}")

    incident = json.loads(r.text)
    message = f'ID: {incident["incident_id"]}\n'\
        f'Status: {incident["incident_status"]}\n'\
        f'Impact: {incident["impact"]}\n'\
        f'Urgency: {incident["urgency"]}\n'\
        f'Description: {incident["description"]}\n'

    context.user_data['incident'] = incident

    reply_keyboard = [
        [InlineKeyboardButton("Add comment", callback_data="add_cmmnt")],
        [InlineKeyboardButton("Change status", callback_data="chng_stts")]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)
    return PROMPT_INCIDENT_ACTION


async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to add a comment to the incident.

    Returns:
    int: The next conversation state.
    """
    query = update.callback_query
    await query.edit_message_text('Type new description')
    return PROMPT_INCIDENT_COMMENT


async def change_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the callback query to change the status of the incident.

    Returns:
    int: The next conversation state.
    """
    incident = context.user_data['incident']
    reply_keyboard = []

    for i in ['Open', 'In Progress', 'Closed']:
        if i != incident["incident_status"]:
            reply_keyboard.append([InlineKeyboardButton(i, callback_data = i)])

    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await update.callback_query.edit_message_text("Choose new status", reply_markup=reply_markup)
    return PROMPT_CHANGE_STATUS

async def prompt_change_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompts the user to select a new status for the incident.

    Returns:
    int: The next conversation state or ConversationHandler.END to end the conversation.
    """
    incident = context.user_data['incident']

    comment = {'incident_id': incident['incident_id'], 'comment': 'User changed status', 
                'created_by': context.user_data['reported_by'],
                'incident_status': update.callback_query.data}
    r = requests.post(BACKEND_URL + '/comments', data=json.dumps(comment), verify=False)
    if r.status_code != 201:
        await update.callback_query.edit_message_text(f"Oops, status code {r.status_code}")
        return ConversationHandler.END

    reply_keyboard = [
        [InlineKeyboardButton("Create Incident", callback_data="Crt_Inc_Bttn")],
        [InlineKeyboardButton("View Incidents", callback_data="Vw_Inc_Bttn")]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await update.callback_query.edit_message_text(f"Status updated. Choose your action", \
                                        reply_markup=reply_markup)
    return PROMPT_ACTION


async def prompt_add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Prompts the user to add a comment to the incident.

    Returns:
    int: The next conversation state.
    """
    message = update.message.text
    incident = context.user_data['incident']
    comment = {'incident_id': incident['incident_id'], 'comment': message, 
                'created_by': context.user_data['reported_by'],
                'incident_status': 'In Progress'}
    r = requests.post(BACKEND_URL + '/comments', data=json.dumps(comment), verify=False)
    if r.status_code != 201:
        await update.message.reply_text(f"Oops, status code {r.status_code}")
        return ConversationHandler.END

    reply_keyboard = [
        [InlineKeyboardButton("Create Incident", callback_data="Crt_Inc_Bttn")],
        [InlineKeyboardButton("View Incidents", callback_data="Vw_Inc_Bttn")]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    await update.message.reply_text(f"{update.message.from_user.first_name}, incident updated. Choose your action", \
                                        reply_markup=reply_markup)
    return PROMPT_ACTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ends the conversation.

    Returns:
    int: ConversationHandler.END to end the conversation.
    """
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PROMPT_ACTION: [
                CallbackQueryHandler(create_incident_callback, pattern="^Crt_Inc_Bttn$"),
                CallbackQueryHandler(view_incidents_callback, pattern="^Vw_Inc_Bttn$"),
                MessageHandler(filters.TEXT, prompt_action),
            ],
            CREATE_INCIDENT: [MessageHandler(filters.TEXT, prompt_incident_description)],
            VIEW_INCIDENT: [CallbackQueryHandler(view_incident)],
            PROMPT_IMPACT: [CallbackQueryHandler(set_impact, pattern="^lev_")],
            PROMPT_URGENCY: [CallbackQueryHandler(set_urgency, pattern="^lev_")],
            PROMPT_INCIDENT_ACTION: [
                CallbackQueryHandler(add_comment, pattern='^add_cmmnt$'),
                CallbackQueryHandler(change_status, pattern='^chng_stts$'),
            ],
            PROMPT_INCIDENT_COMMENT: [MessageHandler(filters.TEXT, prompt_add_comment)],
            PROMPT_CHANGE_STATUS: [CallbackQueryHandler(prompt_change_status)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
    