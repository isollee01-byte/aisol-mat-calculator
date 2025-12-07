import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ----------------------------
# Google Sheets 인증 함수
# ----------------------------
def get_gsheet_client():
    try:
        creds_dict = st.secrets["gcp_service_account"]

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)

        return client

    except Exception as e:
        st.error(f"[ERROR] 구글 인증 실패: {e}")
        return None


# ----------------------------
# Google Sheets 저장 함수
# ----------------------------
def save_to_sheet(data: dict):

    SPREADSHEET_KEY = "1dW_35nI88eyHv8VebJt2slGjKnLA8pUV2s5sRwedXB0"
    SHEET_NAME = "Sheet1"

    try:
        client = get_gsheet_client()
        if client is None:
            st.error("Google 인증 실패로 저장할 수 없습니다.")
            return

        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

        new_row = [
            data.get("date", ""),
            data.get("estimate_id", ""),
            data.get("name", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("size", ""),
            data.get("qty", ""),
            data.get("material", ""),
            data.get("total_cost", "")
        ]

        sheet.append_row(new_row, value_input_option="RAW")
        st.success("Google Sheets 저장 완료!")

    except Exception as e:
        st.error(f"[ERROR] 저장 중 문제 발생: {e}")


# ----------------------------
# Debug 테스트 버튼
# ----------------------------
def debug_google_access():

    st.write("=== DEBUG START ===")
    try:
        creds_email = st.secrets["gcp_service_account"]["client_email"]
        st.write("서비스 계정 이메일:", creds_email)

        client = get_gsheet_client()
        st.write("Google Client 객체:", client)

        SPREADSHEET_KEY = "🔧 여기에 스프레드시트 KEY 입력"

        spreadsheet = client.open_by_key(SPREADSHEET_KEY)
        st.write("스프레드시트 접근 성공:", spreadsheet.title)

    except Exception as e:
        st.error(f"Debug 오류: {e}")

    st.write("=== DEBUG END ===")


# ----------------------------
# 로그인 페이지
# ----------------------------
def login_page():
    st.title("ISOL 견적 프로그램")

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol" and pw == "1234":
            st.session_state["login"] = True
            st.experimental_rerun()
        else:
            st.error("로그인 실패")


# ----------------------------
# 메인 계산기 페이지
# ----------------------------
def calculator():

    st.header("견적 입력")

    name = st.text_input("고객명")
    phone = st.text_input("전화번호")
    address = st.text_input("주소")
    size = st.text_input("사이즈")
    qty = st.number_input("수량", min_value=1, step=1)
    material = st.selectbox("자재", ["TPU", "PU폼", "EPS", "기타"])

    total_cost = qty * 3695560  # 예시 계산식
    st.write(f"최종 견적(VAT 포함): {total_cost:,} 원")

    if st.button("견적서 저장"):
        estimate_id = f"EST-{int(datetime.now().timestamp())}"

        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "estimate_id": estimate_id,
            "name": name,
            "phone": phone,
            "address": address,
            "size": size,
            "qty": qty,
            "material": material,
            "total_cost": total_cost
        }

        save_to_sheet(data)

    st.divider()

    # Debug 버튼
    st.button("🔧 Google Debug Test 실행", on_click=debug_google_access)


# ----------------------------
# Streamlit App Entry
# ----------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_page()
else:
    calculator()
