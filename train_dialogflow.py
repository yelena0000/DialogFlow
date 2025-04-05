import json
import os

from environs import Env
from google.cloud import dialogflow


def create_intent(project_id, display_name, training_phrases_parts, message_texts):
    """Создаёт интент в DialogFlow с вопросами и ответами."""
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)

    training_phrases = []
    for phrase in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(text=phrase)
        training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)

    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message]
    )

    response = intents_client.create_intent(request={"parent": parent, "intent": intent})
    print(f"✅ Создан интент: {response.display_name}")


def main():
    env = Env()
    env.read_env()

    project_id = env.str("DIALOGFLOW_PROJECT_ID")

    with open("questions.json", "r", encoding="utf-8") as file:
        questions_contents = json.load(file)

    for intent_name, intent_data in questions_contents.items():
        questions = intent_data["questions"]
        answer = intent_data["answer"]
        create_intent(project_id, intent_name, questions, [answer])


if __name__ == "__main__":
    main()
