import json

def load_faq_data():
    with open('data/faq.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def handle_faq_command(app):
    faq_data = load_faq_data()

    @app.command("/faq")
    def show_faq(ack, body, client):
        ack()
        # 초기 명령에서 메시지를 보낼 때는 message_ts가 없으므로, 메시지를 새로 보내고 그 타임스탬프를 사용
        response = client.chat_postMessage(
            channel=body["channel_id"],
            text="FAQ를 선택하세요:",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*아래 버튼을 눌러 카테고리를 선택하세요.*"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": cat["name"]
                            },
                            "value": f"{cat['id']}_{cat['name']}",
                            "action_id": f"{cat['id']}_{cat['name']}_button"
                        } for cat in faq_data["categories"]
                    ]
                }
            ]
        )
        # 이후에 block action에서 기존 메시지를 수정할 때는 response["ts"]를 사용
        show_category_menu(client, body["channel_id"], response["ts"], faq_data)

def show_category_menu(client, channel_id, message_ts, faq_data):
    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text="FAQ를 선택하세요:",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*아래 버튼을 눌러 카테고리를 선택하세요.*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": cat["name"]
                        },
                        "value": f"{cat['id']}_{cat['name']}",
                        "action_id": f"{cat['id']}_{cat['name']}_button"
                    } for cat in faq_data["categories"]
                ]
            }
        ]
    )
