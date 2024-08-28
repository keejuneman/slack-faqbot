# slack-faqbot

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 기능

- Slack 명령을 통해 FAQ 카테고리 조회
- 질문 선택 후 상세 답변 제공
- 질문에 대한 답변 후 다시 질문 목록으로 돌아가기 가능

## 설치

1. 리포지토리를 클론합니다.

    ```bash
    git clone https://github.com/yourusername/yourproject.git
    cd yourproject
    ```

2. 필요한 패키지를 설치합니다.

    ```bash
    pip install -r requirements.txt
    ```

3. 환경 변수 파일을 설정합니다.

    `.env` 파일을 프로젝트 루트에 생성하고 다음과 같은 내용을 추가합니다:

    ```env
    SLACK_BOT_TOKEN=your-slack-bot-token
    SLACK_APP_TOKEN=your-slack-app-token
    ```

4. JSON 파일을 설정합니다.

    `data/faq.json` 파일에 FAQ 데이터를 입력합니다. 예시 데이터는 다음과 같습니다:

    ```json
    {
        "categories": [
            {
                "id": "category_1",
                "name": "카테고리 1",
                "questions": [
                    {
                        "id": "category_1_question_1",
                        "question": "질문 1",
                        "answer": "카테고리 1의 질문 1에 대한 답변입니다."
                    }
                ]
            }
        ]
    }
    ```
5. JSON 파일은 `json_edit.py`을 통해 쉽게 수정할 수 있습니다.

    ```bash
      streamlit run json_edit.py

    ```
    ![image](https://github.com/user-attachments/assets/882c5073-eec7-4d56-9945-eaacfb8d5eb3)

6. Bot을 실행합니다.

    ```bash
    python main.py
    ```
## Slack 봇 설정[https://api.slack.com/]

1. OAuth & Permissions
    - Scopes
        - app_mentions:read
        - chat:write
        - chat:write.public
        - commands
2. Socket Mode
    - Enable Socket Mode
3. Slash Commands
    - 원하는 커맨드
