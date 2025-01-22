from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_bolt.oauth.callback_options import CallbackOptions
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
from handlers.faq_handler import handle_faq_command
from handlers.question_handler import register_question_handlers
from handlers.create_thread_handler import register_vacation_handlers  # Import the vacation handler
from slack_bolt.authorization import AuthorizeResult
import os
from dotenv import load_dotenv

# 환경 변수 로드 및 확인
load_dotenv()
client_id = os.getenv("SLACK_CLIENT_ID")
client_secret = os.getenv("SLACK_CLIENT_SECRET")
bot_token = os.getenv("SLACK_BOT_TOKEN")

print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret}")

if not client_id or not client_secret:
    raise ValueError("SLACK_CLIENT_ID 또는 SLACK_CLIENT_SECRET이 .env 파일에 설정되지 않았습니다.")

# authorize 함수 정의
def authorize(enterprise_id, team_id, logger):
    return AuthorizeResult(
        enterprise_id=enterprise_id,
        team_id=team_id,
        bot_token=bot_token,
        bot_user_id="YOUR_BOT_USER_ID"  # 봇 유저 ID 필요
    )

app = App(
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    authorize=authorize  # authorize 함수 사용
)

# Register handlers
handle_faq_command(app)
register_question_handlers(app)
register_vacation_handlers(app)  # Register the vacation handler

# Start the app using Socket Mode
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()