import json
from .faq_handler import show_category_menu

def load_faq_data():
    with open('data/faq.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def register_question_handlers(app):
    faq_data = load_faq_data()

    for cat in faq_data["categories"]:
        create_category_handler(app, cat, faq_data)

def create_category_handler(app, category, faq_data):
    @app.action(f"{category['id']}_{category['name']}_button")
    def handle_category(ack, body, client):
        ack()
        show_question_menu(app, client, body["channel"]["id"], body["message"]["ts"], category, faq_data)

def show_question_menu(app, client, channel_id, message_ts, category, faq_data):
    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"{category['name']}에서 질문을 선택하세요:",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*아래 버튼을 눌러 질문에 대한 답변을 확인하세요.*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": question["question"]
                        },
                        "value": question["id"],
                        "action_id": f"{question['id']}_button"
                    } for question in category["questions"]
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "뒤로가기"
                        },
                        "value": "back_to_categories",
                        "action_id": "back_to_categories_button"
                    }
                ]
            }
        ]
    )

    @app.action("back_to_categories_button")
    def handle_back_to_categories(ack, body, client):
        ack()
        show_category_menu(client, body["channel"]["id"], body["message"]["ts"], faq_data)

    for question in category["questions"]:
        create_question_handler(app, question, category)

def create_question_handler(app, question, category):
    @app.action(f"{question['id']}_button")
    def handle_question(ack, body, client):
        ack()
        show_answer_with_back(app, client, body["channel"]["id"], body["message"]["ts"], question, category)

def show_answer_with_back(app, client, channel_id, message_ts, question, category):
    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=question["answer"],
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": question["answer"]
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "뒤로가기"
                        },
                        "value": f"back_to_questions_{category['id']}",
                        "action_id": f"back_to_questions_{category['id']}_button"
                    }
                ]
            }
        ]
    )

    @app.action(f"back_to_questions_{category['id']}_button")
    def handle_back_to_questions(ack, body, client):
        ack()
        show_question_menu(app, client, body["channel"]["id"], body["message"]["ts"], category, load_faq_data())
