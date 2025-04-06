import logging

from environs import Env
from google.cloud import dialogflow
from telegram import ForceReply, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def detect_intent_text(project_id, session_id, text, language_code='ru'):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Напиши мне что-нибудь, и я отвечу через DialogFlow!')


def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    project_id = context.bot_data['dialogflow_project_id']

    reply = detect_intent_text(project_id, user_id, user_message)
    update.message.reply_text(reply)


def main() -> None:
    env = Env()
    env.read_env()

    tg_bot_token = env.str('TELEGRAM_BOT_TOKEN')
    dialogflow_project_id = env.str('DIALOGFLOW_PROJECT_ID')

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['dialogflow_project_id'] = dialogflow_project_id

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    def safe_handle_message(update: Update, context: CallbackContext) -> None:
        try:
            handle_message(update, context)
        except (GoogleAPICallError, InvalidArgument) as e:
            logger.warning("Ошибка при обращении к DialogFlow: %s", e)
            update.message.reply_text("Ой, я не могу сейчас ответить. Попробуй позже.")
        except Exception as e:
            logger.exception("Неизвестная ошибка:")
            update.message.reply_text("Что-то пошло не так. Напиши позже!")

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, safe_handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

