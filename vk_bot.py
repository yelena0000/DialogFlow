import random

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from google.cloud import dialogflow
from environs import Env


def detect_intent_text(project_id, session_id, text, language_code='ru'):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


def handle_dialogflow(event, vk_api, project_id):
    session_id = str(event.user_id)
    user_message = event.text

    try:
        answer = detect_intent_text(
            project_id=project_id,
            session_id=session_id,
            text=user_message,
            language_code='ru'
        )
    except Exception as e:
        print(f"Ошибка при обращении к DialogFlow: {e}")
        answer = "Произошла ошибка. Попробуйте позже."

    if not answer:
        answer = "Извините, я вас не понял."

    vk_api.messages.send(
        user_id=event.user_id,
        message=answer,
        random_id=random.randint(1, 100000)
    )


def main() -> None:
    env = Env()
    env.read_env()

    vk_group_token = env.str('VK_GROUP_TOKEN')
    dialogflow_project_id = env.str('DIALOGFLOW_PROJECT_ID')

    vk_session = vk.VkApi(token=vk_group_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            handle_dialogflow(event, vk_api, dialogflow_project_id)


if __name__ == "__main__":
    main()
