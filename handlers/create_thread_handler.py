from slack_bolt import App
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
import requests
import io
import json
import os
from dotenv import load_dotenv
import datetime
import time
import slack_sdk
from slack_sdk.web import WebClient
from slack_bolt.context.say.say import Say

def register_vacation_handlers(app: App):
    @app.command("/휴가신청")
    def open_vacation_modal(ack, body, client: WebClient):
        ack()
        trigger_id = body["trigger_id"]
        channel_id = body["channel_id"]
        user_id = body["user_id"]
        
        print(f"휴가신청 명령어 실행 - 채널 ID: {channel_id}, 사용자 ID: {user_id}")
        
        try:
            # 채널 정보 확인 (groups_info 시도)
            try:
                groups_info = client.groups_info(channel=channel_id)
                channel_type = "private_channel"
                print(f"Private 채널 확인됨: {channel_id}")
            except:
                try:
                    # groups_info 실패시 conversations_info 시도
                    channel_info = client.conversations_info(channel=channel_id)
                    channel_type = "private_channel" if channel_info["channel"]["is_private"] else "channel"
                    print(f"채널 타입 확인됨: {channel_type}")
                except:
                    # 모두 실패하면 기본값 사용
                    channel_type = "channel"
                    print("채널 타입 확인 실패, 기본값 사용")
            
            # 모달 열기
            client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "callback_id": "leave_request_modal",
                    "private_metadata": json.dumps({"channel_id": channel_id, "channel_type": channel_type}),
                    "title": {
                        "type": "plain_text",
                        "text": "휴가 신청",
                        "emoji": True
                    },
                    "submit": {
                        "type": "plain_text",
                        "text": "제출",
                        "emoji": True
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "취소",
                        "emoji": True
                    },
                    "blocks": get_modal_blocks(None)
                }
            )
            print(f"모달 열기 성공 - 채널 ID: {channel_id}")
            
        except Exception as e:
            print(f"모달 열기 실패: {e}")
            client.chat_postMessage(
                channel=user_id,
                text="휴가 신청 모달을 열 수 없습니다. 다시 시도해주세요."
            )

    @app.view("leave_request_modal")
    def handle_modal_submission(ack, body, client, logger):
        try:
            # 먼저 ack 호출
            ack()
            
            # 워크스페이스 정보 로깅
            request_team = body.get("team", {})
            request_team_id = request_team.get("id")
            request_team_domain = request_team.get("domain")
            print(f"\n[요청 워크스페이스 정보]")
            print(f"요청 팀 ID: {request_team_id}")
            print(f"요청 팀 도메인: {request_team_domain}")
            
            # 설치된 워크스페이스의 토큰으로 새 클라이언트 생성
            installation = app.installation_store.find_installation(
                enterprise_id=None,
                team_id=request_team_id
            )
            if installation:
                client = WebClient(token=installation.bot_token)
            
            print(f"\n[클라이언트 정보]")
            print(f"클라이언트 토큰: {client.token}")
            
            # 전송 워크스페이스 정보 확인
            try:
                auth_test = client.auth_test()
                print(f"\n[전송 워크스페이스 정보]")
                print(f"전송 팀 ID: {auth_test['team_id']}")
                print(f"전송 팀 이름: {auth_test['team']}")
                print(f"전송 팀 도메인: {auth_test.get('team_domain', 'N/A')}")
            except Exception as e:
                print(f"전송 워크스페이스 정보 조회 실패: {e}")
            
            # view 데이터 추출
            view = body.get("view")
            if not view:
                raise Exception("뷰 데이터를 찾을 수 없습니다.")
            
            # metadata에서 channel_id 추출
            try:
                metadata_str = view.get("private_metadata", "{}")
                metadata = json.loads(metadata_str)
                channel_id = metadata.get("channel_id")
                if not channel_id:
                    raise Exception("채널 ID를 찾을 수 없습니다.")
                
                print(f"\n[채널 정보]")
                print(f"전송할 채널 ID: {channel_id}")
                
            except json.JSONDecodeError:
                raise Exception("메타데이터 형식이 잘못되었습니다.")

            # 메시지 생성 및 전송
            message = (
                f"*출결 정정 신청 스레드*\n\n"
                f"*신청자:* <@{body['user']['id']}>\n"
                f"*유형:* {body['view']['state']['values']['leave_type']['static_select-action']['selected_option']['text']['text']}\n"
                f"*시작일:* {body['view']['state']['values']['start_date']['datepicker-action']['selected_date']}\n"
                f"*종료일:* {body['view']['state']['values']['end_date']['datepicker-action']['selected_date']}\n"
                f"*담당 행정매니저:* {', '.join([f'<@{admin}>' for admin in body['view']['state']['values']['admin_selector']['multi_users_select-action']['selected_users']])}"
            )
            
            result = client.chat_postMessage(
                channel=channel_id,
                text=message
            )
            
            print(f"\n[메시지 전송 결과]")
            print(f"전송 성공 여부: {bool(result.get('ok'))}")
            print(f"메시지 ts: {result.get('ts')}")
            
        except Exception as e:
            print(f"\n[에러 발생]")
            print(f"Error in modal submission: {str(e)}")


    def upload_to_drive(file_info, client, values, user_name):
        try:
            load_dotenv()
            service_account_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY'))
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            drive_service = build('drive', 'v3', credentials=credentials)
            folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

            # Slack에서 파일 다운로드
            response = client.files_info(file=file_info['id'])
            file_url = response['file']['url_private_download']
            headers = {'Authorization': f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
            file_response = requests.get(file_url, headers=headers)

            # 원본 파일의 확장자 추출
            original_filename = file_info['name']
            file_extension = original_filename.split('.')[-1] if '.' in original_filename else ''

            # 새로운 파일 이름 생성
            course_name = values["course_type"]["course_select-action"]["selected_option"]["text"]["text"]
            course_number = values["number_input"]["number-action"]["value"]
            new_filename = f"{course_name}_{course_number}기_{user_name}.{file_extension}"

            # 파일 메타데이터 설정
            file_metadata = {
                'name': new_filename,
                'parents': [folder_id]
            }

            # 파일 데이터 준비
            file_data = io.BytesIO(file_response.content)
            media = MediaIoBaseUpload(
                file_data,
                mimetype=file_info['mimetype'],
                resumable=True
            )

            # 구글 드라이브에 파일 업로드
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            return file.get('webViewLink')  # 파일의 웹 뷰 링크 반환

        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")
            return None

    def update_google_sheet(values, user_id, client):
        max_retries = 3
        retry_delay = 2  # 초 단위

        for attempt in range(max_retries):
            try:
                load_dotenv()
                service_account_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_SHEETS'))
                
                SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=SCOPES
                )
                
                service = build('sheets', 'v4', credentials=credentials)
                sheet = service.spreadsheets()

                # A열의 데이터를 읽어서 첫 번째 빈 행 찾기
                try:
                    result = sheet.values().get(
                        spreadsheetId='1Qd4-EZ8fAu_FRiUDBZ5i6O1g-blWXiNbzqKe0-7bTfk',
                        range='통합!A5:A1000'  # A5부터 A1000까지 검사
                    ).execute()
                except Exception as e:
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면
                        print(f"시트 읽기 시도 {attempt + 1} 실패, {retry_delay}초 후 재시도...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise e  # 모든 재시도 실패시 예외 발생

                # 첫 번째 빈 행 번호 찾기
                values_in_a = result.get('values', [])
                next_row = 5  # 기본값은 5행
                
                if values_in_a:
                    next_row = len(values_in_a) + 5  # 데이터가 있는 마지막 행 다음 행

                # 사용자 정보 가져오기
                user_info = client.users_info(user=user_id)
                user_name = user_info['user']['real_name']
                user_email = user_info['user']['profile']['email'] 

                # 현재 타임스탬프
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 파일 업로드 및 드라이브 링크 가져오기
                drive_link = ""
                if "file_upload" in values and "file_input-action" in values["file_upload"]:
                    files = values["file_upload"]["file_input-action"].get("files", [])
                    if files:
                        file_info = files[0]
                        drive_link = upload_to_drive(file_info, client, values, user_name) or ""

                # LM 상담 체크박스 상태
                lm_consulted = bool(values.get("lm_check", {}).get("checkbox-action", {}).get("selected_options"))

                # 데이터 준비
                row_data = [
                    [
                        timestamp,
                        user_email, 
                        str(lm_consulted),
                        values["course_type"]["course_select-action"]["selected_option"]["text"]["text"],
                        values["number_input"]["number-action"]["value"],
                        values["phone_input"]["phone-action"]["value"],
                        values["leave_type"]["static_select-action"]["selected_option"]["text"]["text"].split('-')[0].strip(),
                        drive_link,
                        f"{values['start_date']['datepicker-action']['selected_date']} ~ {values['end_date']['datepicker-action']['selected_date']}",
                        user_name
                    ]
                ]

                # 특정 행에 데이터 업데이트
                range_name = f'통합!A{next_row}:J{next_row}'
                try:
                    result = sheet.values().update(
                        spreadsheetId='1Qd4-EZ8fAu_FRiUDBZ5i6O1g-blWXiNbzqKe0-7bTfk',
                        range=range_name,
                        valueInputOption='RAW',
                        body={'values': row_data}
                    ).execute()
                except Exception as e:
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면
                        print(f"시트 업데이트 시도 {attempt + 1} 실패, {retry_delay}초 후 재시도...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise e  # 모든 재시도 실패시 예외 발생

                print(f"Data written to row {next_row}")
                return True

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"시도 {attempt + 1} 실패: {e}")
                    time.sleep(retry_delay)
                else:
                    print(f"모든 재시도 실패: {e}")
                    return False

    def create_thread(ack, body, client):
        try:
            ack()
            values = body["view"]["state"]["values"]
            
            # ... 기존 코드 ...
            
            # 구글 시트 업데이트
            sheet_updated = update_google_sheet(values)
            
            if not sheet_updated:
                # 시트 업데이트 실패 시 에러 메시지 추가
                message += "\n\n:warning: *구글 시트 업데이트 실패*"
            
            # ... 나머지 기존 코드 ...

        except Exception as e:
            print(f"Error: {e}")

    # 휴가 유형 선택 시 실행되는 액션 핸들러 추가
    @app.action("static_select-action")
    def handle_leave_type_selection(ack, body, client):
        ack()
        selected_option = body["actions"][0]["selected_option"]["text"]["text"]
        print(f"Selected leave type: {selected_option}")  # 디버깅을 위한 출력
        
        view = client.views_update(
            view_id=body["view"]["id"],
            hash=body["view"]["hash"],
            view={
                "type": "modal",
                "callback_id": "leave_request_modal",
                "private_metadata": body["view"].get("private_metadata", ""),
                "title": {
                    "type": "plain_text",
                    "text": "휴가 신청",
                    "emoji": True
                },
                "submit": {
                    "type": "plain_text",
                    "text": "제출",
                    "emoji": True
                },
                "close": {
                    "type": "plain_text",
                    "text": "취소",
                    "emoji": True
                },
                "blocks": get_modal_blocks(selected_option)
            }
        )

    def get_modal_blocks(leave_type):
        # 기본 블록 구성
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*휴가 신청 절차*\n1. 담당 러닝 매니저와 휴가 일정 상담 진행\n2. *<https://sincere-nova-ec6.notion.site/a8bbcb69d87c4c19aabee16c6a178286|휴가계획서 및 출석 대장 작성>*\n3.아래 항목 작성 및 증빙서류 첨부 후 제출"
                }
            },
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "lm_check",
                "element": {
                    "type": "checkboxes",
                    "action_id": "checkbox-action",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "담당 LM님과 휴가 사용과 관련하여 상담이 진행되었나요?",
                                "emoji": True
                            },
                            "value": "lm_consulted"
                        }
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": " ",  # 빈 레이블을 사용하여 체크박스 텍스트만 표시
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "leave_type",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an item",
                        "emoji": True
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "휴가",
                                "emoji": True
                            },
                            "value": "value-0"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "병가",
                                "emoji": True
                            },
                            "value": "value-1"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "공가 - 훈련 및 시험, 공민권 등",
                                "emoji": True
                            },
                            "value": "value-2"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "공가 - 결혼",
                                "emoji": True
                            },
                            "value": "value-3"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "공가 - 사망(가족관계증명서, 사망진단서 必)",
                                "emoji": True
                            },
                            "value": "value-4"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "공가 - 출산",
                                "emoji": True
                            },
                            "value": "value-5"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "공가 - 예비군",
                                "emoji": True
                            },
                            "value": "value-6"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "공가 - 기타",
                                "emoji": True
                            },
                            "value": "value-7"
                        }
                    ],
                    "action_id": "static_select-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": ":umbrella_on_ground: 휴가 유형을 선택해주세요",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "course_type",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "참여하고 있는 과정명을 선택해주세요.",
                        "emoji": True
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "(커널, 백엔드)백엔드 개발 부트캠프",
                                "emoji": True
                            },
                            "value": "backend-kernel"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "(커널)프론트엔드 개발 중급 부트캠프",
                                "emoji": True
                            },
                            "value": "frontend-kernel"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "데브캠프 : 백엔드 (AI 융합 백엔드 개발 부트캠프)",
                                "emoji": True
                            },
                            "value": "backend-ai"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "[BE] 핀테크 서비스 백엔드 개발 부트캠프(백엔드)",
                                "emoji": True
                            },
                            "value": "backend-fintech"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "[PM] 프로덕트 매니저(PM) 부트캠프",
                                "emoji": True
                            },
                            "value": "pm"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "AI(인공지능) Lab",
                                "emoji": True
                            },
                            "value": "ai-lab"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "[SM-BDA] 데이터 분석 부트캠프",
                                "emoji": True
                            },
                            "value": "data-analytics"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "데브캠프 : 프론트엔드 개발",
                                "emoji": True
                            },
                            "value": "frontend"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "UXUI 디자인 부트캠프",
                                "emoji": True
                            },
                            "value": "uxui"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "INNER CIRCLE : 개발 Course",
                                "emoji": True
                            },
                            "value": "inner-circle-dev"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "INNER CIRCLE : 기획/디자인 Course",
                                "emoji": True
                            },
                            "value": "inner-circle-design"
                        }
                    ],
                    "action_id": "course_select-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "코스를 선택해주세요",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "number_input",
                "element": {
                    "type": "number_input",
                    "is_decimal_allowed": False,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "회차를 입력해주세요",
                        "emoji": True
                    },
                    "action_id": "number-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "회차를 입력해주세요",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "phone_input",
                "element": {
                    "type": "plain_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "전화번호를 입력해주세요 (예: 010-1234-5678)",
                        "emoji": True
                    },
                    "action_id": "phone-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "전화번호",
                    "emoji": True
                }
            },
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "start_date",
                "element": {
                    "type": "datepicker",
                    "initial_date": "2024-01-01",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date",
                        "emoji": True
                    },
                    "action_id": "datepicker-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "휴가 시작일",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "end_date",
                "element": {
                    "type": "datepicker",
                    "initial_date": "2024-01-01",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select a date",
                        "emoji": True
                    },
                    "action_id": "datepicker-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "휴가 종료일 (당일 휴가의 경우 시작일과 동일하게 설정)",
                    "emoji": True
                }
            },
            {"type": "divider"},
            {
                "type": "input",
                "block_id": "admin_selector",
                "element": {
                    "type": "multi_users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select users",
                        "emoji": True
                    },
                    "action_id": "multi_users_select-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "담당 행정매니저를 선택해주세요",
                    "emoji": True
                }
            },
            {"type": "divider"},
        ]
        
        # 정확한 '휴가' 텍스트 매칭
        if leave_type == "휴가":
            print(f"Adding file upload block for leave type: {leave_type}")  # 디버깅을 위한 출력
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "input",
                    "block_id": "file_upload",
                    "element": {
                        "type": "file_input",
                        "action_id": "file_input-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "증빙서류를 첨부해주세요",
                        "emoji": True
                    }
                }
            ])
        
        return blocks

