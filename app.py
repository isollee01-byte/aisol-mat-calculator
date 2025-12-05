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
# Airtable 설정 - Base / Table / View ID
# --------------------------------------------------------
AIRTABLE_API_TOKEN = st.secrets["AIRTABLE_API_TOKEN"]
AIRTABLE_BASE_ID = "appVMI6Ut8YkQHgC2"
AIRTABLE_TABLE_ID = "tblRmPhqtxpBy2YkM"
AIRTABLE_VIEW_ID = "viwY70EsVC8zhXP29"

# --------------------------------------------------------
# Airtable 저장 함수
# --------------------------------------------------------
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
# 로고 표시용 Base64 변환 함수
# --------------------------------------------------------
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def show_logo_top():
    try:
        logo_base64 = get_base64("isol_logo.png")
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:-20px;">
                <img src="data:image/png;base64,{logo_base64}" width="120">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        pass


def show_watermark():
    try:
        logo_base64 = get_base64("isol_logo.png")
        st.markdown(
            f"""
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                opacity: 0.08;">
                <img src="data:image/png;base64,{logo_base64}" width="160">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        pass


# --------------------------------------------------------
# 로그인 기능
# --------------------------------------------------------
def login_screen():
    st.markdown("<h2 style='text-align:center;'>아이솔(ISOL) 견적 시스템 로그인</h2>", unsafe_allow_html=True)
    st.write("승인된 사용자만 접근할 수 있습니다.")
    show_logo_top()

    id_input = st.text_input("아이디")
    pw_input = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if id_input == "isol_admin" and pw_input == "isol202512!":
            st.session_state["login"] = True
            st.success("로그인 성공!")
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


# --------------------------------------------------------
# 간편모드 계산
# --------------------------------------------------------
def simple_mode_calc(pyeong, area_type, expand_type):
    area_factor = {"거실": 0.93, "거실+복도": 1.46, "거실+복도+아이방1": 1.67, "거실+복도+주방": 2}
    base_factor = area_factor[area_type]

    mats = pyeong * base_factor

    # 실측 손실 반영 룰
    if mats - int(mats) <= 0.3:
        mats = int(mats)
    elif mats - int(mats) >= 0.6:
        mats = int(mats) + 1
    else:
        mats = math.ceil(mats)

    mats = int(mats * 1.10)  # +10% 넉넉히
    if expand_type == "비확장형":
        mats -= 8
    return max(mats, 0)


# --------------------------------------------------------
# 정밀모드 계산
# --------------------------------------------------------
def precision_mode_calc(measurements):
    total = 0
    for w, h in measurements:
        row = w / 80
        col = h / 80

        row = math.ceil(row - 0.3) if row - int(row) > 0.3 else math.floor(row)
        col = math.ceil(col - 0.3) if col - int(col) > 0.3 else math.floor(col)

        total += max(row, 1) * max(col, 1)
    return total


# --------------------------------------------------------
# 메인 견적 계산 화면
# --------------------------------------------------------
def calculator():
    show_logo_top()
    st.markdown("<h1 style='text-align:center;'>아이솔(ISOL) 800×800 매트 견적 프로그램</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;'>간편측정 · 실제측정 기반 프리미엄 매트 견적 산출</h4>", unsafe_allow_html=True)

    show_watermark()

    st.subheader("🧾 고객 정보")
    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")

    # 주소 입력
    if st.button("📍 주소 검색(카카오)"):
        st.markdown(
            """
            <script>
            new daum.Postcode({
                oncomplete: function(data) {
                    var fullAddr = data.address;
                    window.parent.postMessage({type:"ADDRESS", value:fullAddr}, "*");
                }
            }).open();
            </script>
            """,
            unsafe_allow_html=True
        )

    selected_address = st.text_input("선택된 주소")
    detail_address = st.text_input("상세 주소 (동/호수 등)")
    install_date = st.date_input("시공 희망일 선택")

    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("계산 모드", ["간편측정", "실제측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1, step=1)
        area_type = st.selectbox("시공 범위 선택", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])
        if st.button("계산하기"):
            total_mats = simple_mode_calc(pyeong, area_type, expand_type)
            st.success(f"총 필요 매트 수량: {total_mats}장")

    else:
        st.subheader("실측 입력 (cm 단위)")
        count = st.number_input("구역 개수", min_value=1, step=1)
        measurements = []
        for i in range(count):
            w = st.number_input(f"{i+1}번 구역 가로(cm)", min_value=1)
            h = st.number_input(f"{i+1}번 구역 세로(cm)", min_value=1)
            measurements.append((w, h))

        if st.button("계산하기"):
            total_mats = precision_mode_calc(measurements)
            st.success(f"정밀 계산된 매트 수량: {total_mats}장")

    # -------------------------------------------------------------
    # 견적서 출력 & Airtable 저장
    # -------------------------------------------------------------
    if total_mats > 0:
        st.subheader("📄 견적서 생성")

        material_cost = total_mats * 40000
        work_cost = int(material_cost * 0.165)
        final_cost = material_cost + work_cost

        st.write(f"총 필요한 매트 수: **{total_mats}장**")
        st.write(f"재료비: **{material_cost:,} 원**")
        st.write(f"시공비: **{work_cost:,} 원**")
        st.write(f"최종 견적(VAT 포함): **{final_cost:,} 원**")

        quote_id = f"Q-{datetime.now().strftime('%Y%m%d-%H%M')}"

        if st.button("견적서 Airtable 저장"):
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

        if st.button("견적서 인쇄하기"):
            st.markdown("<script>window.print()</script>", unsafe_allow_html=True)


# --------------------------------------------------------
# 페이지 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()
