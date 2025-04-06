import random
import logging

from environs import Env
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
from google.cloud import dialogflow
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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

    return response.query_result


def handle_dialogflow_answer(event, vk_api, project_id, language_code='ru'):
    session_id = str(event.user_id)
    query_result = detect_intent_text(project_id, session_id, event.text, language_code)

    if not query_result.intent.is_fallback:
        vk_api.messages.send(
            user_id=event.user_id,
            message=query_result.fulfillment_text,
            random_id=random.randint(1, 100000)
        )


def main():
    env = Env()
    env.read_env()

    vk_group_token = env.str('VK_GROUP_TOKEN')
    dialogflow_project_id = env.str('DIALOGFLOW_PROJECT_ID')
    tg_bot_token = env.str('TG_BOT_TOKEN')
    chat_id = env.str('TG_CHAT_ID')

    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                handle_dialogflow_answer(event, vk_api, dialogflow_project_id)
            except (GoogleAPICallError, InvalidArgument) as e:
                logger.warning("Ошибка при обращении к DialogFlow: %s", e)
                send_error_to_telegram(str(e), tg_bot_token, chat_id)
            except Exception as e:
                logger.exception("Неизвестная ошибка при обработке сообщения")
                send_error_to_telegram(str(e), tg_bot_token, chat_id)


if __name__ == "__main__":
    main()
