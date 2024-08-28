import json
import os
import streamlit as st

# JSON 파일 경로 설정
DATA_DIR = "data"
JSON_FILE_PATH = os.path.join(DATA_DIR, "faq.json")

# JSON 파일 로드
def load_json():
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {"categories": []}

# JSON 파일 저장
def save_json(data):
    # 기본적인 유효성 검사 추가
    for category in data.get("categories", []):
        if not category.get("name"):
            st.error("카테고리 이름이 비어 있습니다.")
            return
        for question in category.get("questions", []):
            if not question.get("question") or not question.get("answer"):
                st.error("질문 또는 답변이 비어 있습니다.")
                return

    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.success(f"파일이 저장되었습니다: {JSON_FILE_PATH}")

# JSON 데이터 표시
def display_json(data):
    categories = data.get("categories", [])
    for category in categories:
        st.subheader(f"카테고리: {category['name']}")
        for question in category.get("questions", []):
            st.write(f"질문: {question['question']}")
            st.write(f"답변: {question['answer']}")
            st.write("=============================================================")

# JSON 데이터 수정 및 추가
def modify_json(data):
    st.sidebar.header("수정/추가 메뉴")
    action = st.sidebar.selectbox("수행할 작업을 선택하세요", ["카테고리 추가", "카테고리 수정", "질문 추가", "질문 수정"])

    if action == "카테고리 추가":
        new_cat_name = st.sidebar.text_input("새 카테고리 이름")
        if st.sidebar.button("카테고리 추가"):
            new_category = {
                "id": f"category_{len(data['categories']) + 1}",
                "name": new_cat_name,
                "questions": []
            }
            data['categories'].append(new_category)
            save_json(data)
            st.experimental_rerun()

    if action == "카테고리 수정":
        selected_category = st.sidebar.selectbox("수정할 카테고리 선택", [cat['name'] for cat in data['categories']])
        new_cat_name = st.sidebar.text_input("새 카테고리 이름", selected_category)
        if st.sidebar.button("카테고리 수정"):
            for cat in data['categories']:
                if cat['name'] == selected_category:
                    cat['name'] = new_cat_name
                    break
            save_json(data)
            st.experimental_rerun()

    if action == "질문 추가":
        selected_category = st.sidebar.selectbox("질문을 추가할 카테고리 선택", [cat['name'] for cat in data['categories']])
        new_question = st.sidebar.text_input("새 질문")
        new_answer = st.sidebar.text_area("새 답변")
        if st.sidebar.button("질문 추가"):
            for cat in data['categories']:
                if cat['name'] == selected_category:
                    new_question_data = {
                        "id": f"{cat['id']}_question_{len(cat['questions']) + 1}",
                        "question": new_question,
                        "answer": new_answer
                    }
                    cat['questions'].append(new_question_data)
                    break
            save_json(data)
            st.experimental_rerun()

    if action == "질문 수정":
        selected_category = st.sidebar.selectbox("질문이 속한 카테고리 선택", [cat['name'] for cat in data['categories']])
        selected_question = None
        for cat in data['categories']:
            if cat['name'] == selected_category:
                selected_question = st.sidebar.selectbox("수정할 질문 선택", [q['question'] for q in cat['questions']])
                break
        new_question_text = st.sidebar.text_input("새 질문 내용", selected_question)
        new_answer_text = st.sidebar.text_area("새 답변 내용")
        if st.sidebar.button("질문 수정"):
            for cat in data['categories']:
                if cat['name'] == selected_category:
                    for q in cat['questions']:
                        if q['question'] == selected_question:
                            q['question'] = new_question_text
                            q['answer'] = new_answer_text
                            break
            save_json(data)
            st.experimental_rerun()

# 메인 함수
def main():
    st.title("JSON 파일 수정 및 추가 도구")
    st.write(":red[**JSON 파일 수정 후 Slack BOT Reboot 필수**]")
    # JSON 파일 로드
    data = load_json()
    st.write("현재 JSON 파일의 내용:")
    display_json(data)
    
    # JSON 데이터 수정 및 추가
    modify_json(data)

if __name__ == "__main__":
    # data 디렉토리가 존재하지 않으면 생성
    os.makedirs(DATA_DIR, exist_ok=True)
    main()
