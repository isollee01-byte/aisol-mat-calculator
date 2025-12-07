import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


# ----------------------------
# Google Sheets 인증
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
        st.error(f"[ERROR] Google 인증 실패: {e}")
        return None


# ----------------------------
# Google Sheets 저장 함수
# ----------------------------
def save_to_sheet(data: dict):
    SPREADSHEET_KEY = "1dW_35nI88eyHv8VebJt2slGjKnLA8pUV2s5sRwedXB0"  # 🔧 회장님 키 입력
    SHEET_NAME = "Sheet1"   # 🔧 실제 시트 이름

    try:
        client = get_gsheet_client()
        if client is None:
            st.error("Google 인증 실패로 저장 중단됨.")
            return

        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)

        new_row = [
            data.get("timestamp", ""),
            data.get("estimate_id", ""),
            data.get("name", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("size", ""),
            data.get("qty", ""),
            data.get("material", ""),
            data.get("total_cost", ""),
        ]

        sheet.append_row(new_row, value_input_option="RAW")
        st.success("Google Sheets 저장 성공!")

    except Exception as e:
        st.error(f"[ERROR] 시트 저장 실패: {e}")


# ----------------------------
# 🔧 디버그 함수 — 로그인 후에만 보여줌
# ----------------------------
def debug_google_access():

    st.subheader("🔧 Google Debug Test")

    try:
        st.write("서비스 계정 이메일:", st.secrets["gcp_service_account"]["client_email"])
    except:
        st.error("서비스 계정 이메일 로딩 실패")

    try:
        client = get_gsheet_client()
        st.write("Google Client:", client)

        SPREADSHEET_KEY = "1dW_35nI88eyHv8VebJt2slGjKnLA8pUV2s5sRwedXB0"

        sh = client.open_by_key(SPREADSHEET_KEY)
        st.success(f"스프레드시트 접근 성공: {sh.title}")

    except Exception as e:
        st.error(f"Debug 오류: {e}")


# ----------------------------
# 로그인 페이지
# ----------------------------
def login_page():

    st.title("ISOL 견적 프로그램")

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol" and pw == "1234":   # 🔧 회장님 맞게 수정 가능
            st.session_state["login"] = True
            st.experimental_rerun()
        else:
            st.error("로그인 실패")


# ----------------------------
# 견적 계산 페이지
# ----------------------------
def calculator():

    st.header("견적 입력")

    name = st.text_input("고객명")
    phone = st.text_input("전화번호")
    address = st.text_input("주소")

    size = st.text_input("매트 크기")
    qty = st.number_input("매트 수량", min_value=1, step=1)
    material = st.selectbox("재질", ["TPU", "PU", "Fabric", "기타"])

    total_cost = qty * 30000  # 🔧 임시 계산 예시
    st.write(f"총 견적(VAT 포함): {total_cost:,} 원")

    if st.button("견적 저장"):
        estimate_id = f"EST-{int(datetime.now().timestamp())}"

        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
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

    # 로그인 후에만 디버그 버튼 보이게
    st.button("🔧 Google Debug Test 실행", on_click=debug_google_access)


# ----------------------------
# APP ENTRY
# ----------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_page()
else:
    calculator()
