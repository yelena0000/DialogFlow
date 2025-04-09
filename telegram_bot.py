import logging

from environs import Env
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
from google.cloud import dialogflow
from telegram import ForceReply, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

logger = logging.getLogger(__file__)


def send_error_to_telegram(error_message, tg_bot_token, chat_id):
    from telegram import Bot
    bot = Bot(token=tg_bot_token)
    bot.send_message(chat_id=chat_id, text=f"❗ Ошибка: {error_message}")


def detect_intent_text(project_id, session_id, text, language_code='ru'):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('Напиши мне что-нибудь, и я отвечу через DialogFlow!')


def handle_message(update: Update, context: CallbackContext):
    try:
        user_message = update.message.text
        session_id = f"tg-{update.effective_user.id}"
        project_id = context.bot_data['dialogflow_project_id']

        reply = detect_intent_text(project_id, session_id, user_message)
        update.message.reply_text(reply)

    except (GoogleAPICallError, InvalidArgument) as e:
        logger.warning("Ошибка при обращении к DialogFlow: %s", e)
        update.message.reply_text("Ой, я не могу сейчас ответить. Попробуй позже.")
        send_error_to_telegram(str(e), context.bot.token, context.bot_data['chat_id'])
    except Exception as e:
        logger.exception("Неизвестная ошибка:")
        update.message.reply_text("Что-то пошло не так. Напиши позже!")
        send_error_to_telegram(str(e), context.bot.token, context.bot_data['chat_id'])


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.setLevel(logging.DEBUG)

    env = Env()
    env.read_env()

    tg_bot_token = env.str('TG_BOT_TOKEN')
    dialogflow_project_id = env.str('DIALOGFLOW_PROJECT_ID')
    chat_id = env.str('TG_CHAT_ID')

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['dialogflow_project_id'] = dialogflow_project_id
    dispatcher.bot_data['chat_id'] = chat_id

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
