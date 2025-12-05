import streamlit as st
import math
import base64
import requests
from datetime import datetime

st.set_page_config(
    page_title="아이솔(ISOL) 800×800 매트 견적 프로그램",
    layout="centered",
)

# --------------------------------------------------------
# Airtable 설정 - Base / Table
# --------------------------------------------------------
AIRTABLE_API_TOKEN = st.secrets["AIRTABLE_API_TOKEN"]
AIRTABLE_BASE_ID = "appVMI6Ut8YkQHgC2"
AIRTABLE_TABLE_ID = "tblRmPhqtxpBy2YkM"   # Quotes 테이블

def save_to_airtable(record):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"fields": record}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# --------------------------------------------------------
# 로고 & 워터마크
# --------------------------------------------------------
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def show_logo_top():
    try:
        logo_base64 = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:-10px;">
                <img src="data:image/png;base64,{logo_base64}" width="130">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        st.write("로고 파일 로드 실패")

def show_watermark():
    try:
        logo_base64 = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="
                position: fixed;
                bottom: 25px;
                right: 25px;
                opacity: 0.08;
                z-index: 9999;">
                <img src="data:image/png;base64,{logo_base64}" width="180">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        st.write("워터마크 오류")

# --------------------------------------------------------
# 로그인
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown("<h2 style='text-align:center;'>아이솔(ISOL) 견적 시스템 로그인</h2>", unsafe_allow_html=True)
    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol_admin" and pw == "isol202512!":
            st.session_state["login"] = True
            st.success("로그인 성공!")
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# --------------------------------------------------------
# 계산 로직
# --------------------------------------------------------
def simple_mode_calc(pyeong, area_type, expand_type):
    factor = {"거실": 0.93, "거실+복도": 1.46, "거실+복도+아이방1": 1.67, "거실+복도+주방": 2}
    mats = pyeong * factor[area_type]

    # 실측 반영 규칙
    if mats - int(mats) <= 0.3:
        mats = int(mats)
    elif mats - int(mats) >= 0.6:
        mats = int(mats) + 1
    else:
        mats = math.ceil(mats)

    mats = int(mats * 1.10)
    if expand_type == "비확장형":
        mats -= 8
    return max(mats, 0)

def precision_mode_calc(measurements):
    total = 0
    for w, h in measurements:
        row = math.ceil(max(w/80, 1))
        col = math.ceil(max(h/80, 1))
        total += row * col
    return total

# --------------------------------------------------------
# 메인 화면
# --------------------------------------------------------
def calculator():
    show_logo_top()
    show_watermark()

    st.markdown("<h1 style='text-align:center;'>아이솔 800×800 매트 견적 프로그램</h1>", unsafe_allow_html=True)

    # -----------------------------
    # 주소 검색 기능 — 완전 수정된 버전
    # -----------------------------
    js_code = """
    <script>
    function openKakaoPostcode() {
        new daum.Postcode({
            oncomplete: function(data) {
                const addr = data.address;
                window.parent.postMessage({type: 'kakao_address', address: addr}, "*");
            }
        }).open();
    }
    </script>
    """
    st.components.v1.html(js_code, height=0)

    st.subheader("🧾 고객 정보")

    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")

    st.markdown(
        '<button onclick="openKakaoPostcode()" style="padding:8px 15px; background:#4A90E2; color:white; border:none; border-radius:5px;">📍 주소 검색</button>',
        unsafe_allow_html=True
    )

    selected_address = st.text_input("선택된 주소", key="address_box")
    detail_address = st.text_input("상세 주소 입력")

    # JS → Streamlit 주소 전달 처리
    st.markdown(
        """
        <script>
        window.addEventListener("message", (event) => {
            if (event.data.type === "kakao_address") {
                const addrBox = window.parent.document.querySelector('input[id="address_box"]');
                if (addrBox) { addrBox.value = event.data.address; }
            }
        });
        </script>
        """,
        unsafe_allow_html=True,
    )

    install_date = st.date_input("시공 희망일")

    st.subheader("📌 계산 모드")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1, step=1)
        area_type = st.selectbox("시공 범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc(pyeong, area_type, expand_type)
            st.success(f"필요 매트: {total_mats}장")

    else:
        cnt = st.number_input("측정 구역 수", min_value=1)
        measurements = []
        for i in range(cnt):
            w = st.number_input(f"{i+1} 구역 가로(cm)", min_value=1)
            h = st.number_input(f"{i+1} 구역 세로(cm)", min_value=1)
            measurements.append((w, h))

        if st.button("계산하기"):
            total_mats = precision_mode_calc(measurements)
            st.success(f"정밀 계산된 매트 수: {total_mats}장")

    # ----------------------------------------------------
    # 견적서 출력 + Airtable 저장
    # ----------------------------------------------------
    if total_mats > 0:
        material_cost = total_mats * 40000
        work_cost = int(material_cost * 0.165)
        final_cost = material_cost + work_cost

        st.subheader("📄 견적 결과")
        st.write(f"총 매트 수량: **{total_mats}장**")
        st.write(f"재료비: **{material_cost:,} 원**")
        st.write(f"시공비: **{work_cost:,} 원**")
        st.write(f"최종 견적(VAT 포함): **{final_cost:,} 원**")

        quote_id = f"Q-{datetime.now().strftime('%Y%m%d-%H%M')}"

        if st.button("💾 Airtable 저장"):
            record = {
                "Quote ID": quote_id,
                "Customer Name": customer_name,
                "Phone Number": customer_phone,
                "Address": selected_address + " " + detail_address,
                "Installation Date": str(install_date),
                "Calculation Mode": mode,
                "Total Materials": total_mats,
                "Total Price": final_cost,
            }
            save_to_airtable(record)
            st.success("Airtable 저장 완료!")

        if st.button("🖨 인쇄하기"):
            st.markdown("<script>window.print()</script>", unsafe_allow_html=True)


# --------------------------------------------------------
# 실행부
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()
