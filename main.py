import os

import telegram
from environs import Env
from google.cloud import dialogflow


def detect_intent_texts(project_id, session_id, texts, language_code):
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    print("Session path: {}\n".format(session))

    for text in texts:
        text_input = dialogflow.TextInput(
            text=text,
            language_code=language_code
        )
        query_input = dialogflow.QueryInput(
            text=text_input
        )
        response = session_client.detect_intent(
            request={
                "session": session,
                "query_input": query_input
            }
        )
        query_result = response.query_result

        print("=" * 20)
        print(
            f"Query text: {query_result.query_text}\n\n"
            f"Detected intent: {query_result.intent.display_name} "
            f"(confidence: {query_result.intent_detection_confidence})\n"
            f"Fulfillment text: {query_result.fulfillment_text}\n"
        )


def main():
    env = Env()
    env.read_env()

    project_id = env.str('DIALOGFLOW_PROJECT_ID')
    session_id = 'test-session-123'
    texts = ['Хеллоу']
    language_code = "ru"

    detect_intent_texts(project_id, session_id, texts, language_code)


if __name__ == '__main__':
    main()