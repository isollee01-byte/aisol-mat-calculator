import streamlit as st
import math
import base64
from datetime import datetime

st.set_page_config(
    page_title="아이솔(ISOL) 800×800 매트 견적 프로그램",
    layout="centered",
)

# --------------------------------------------------------
# 로고 & 워터마크
# --------------------------------------------------------
def get_base64(bin_file):
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo_top():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="text-align:center;">
                <img src="data:image/png;base64,{logo}" width="130">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        st.error("로고 파일이 없습니다. isollogo.png 파일을 같은 폴더에 두세요.")

def show_watermark():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                opacity: 0.08;
                z-index: 999;">
                <img src="data:image/png;base64,{logo}" width="160">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        pass

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
            st.error("아이디 또는 비밀번호가 틀렸습니다.")

# --------------------------------------------------------
# 계산 로직
# --------------------------------------------------------
def simple_mode_calc(pyeong, area_type, expand_type):
    factor = {"거실": 0.93, "거실+복도": 1.46, "거실+복도+아이방1": 1.67, "거실+복도+주방": 2}
    mats = pyeong * factor[area_type]

    if mats - int(mats) <= 0.3:
        mats = int(mats)
    elif mats - int(mats) >= 0.6:
        mats = int(mats) + 1
    else:
        mats = math.ceil(mats)

    mats = int(mats * 1.10)    # 여유량 10%

    if expand_type == "비확장형":
        mats -= 8

    return max(mats, 0)

# --------------------------------------------------------
# Kakao 주소검색 (iframe 방식)
# --------------------------------------------------------
def address_iframe():
    st.markdown(
        """
        <iframe src="https://postcode.map.daum.net/guide" 
                style="width:100%; height:350px; border:1px solid #ddd; border-radius:6px;">
        </iframe>
        """,
        unsafe_allow_html=True
    )
    st.info("※ 위에서 검색한 주소를 직접 복사하여 아래 입력창에 붙여넣어 주세요.")

# --------------------------------------------------------
# 메인 화면
# --------------------------------------------------------
def calculator():
    show_logo_top()
    show_watermark()

    st.markdown("<h1 style='text-align:center;'>아이솔(ISOL) 800×800 매트 견적 프로그램</h1>", unsafe_allow_html=True)

    st.subheader("🧾 고객 정보")
    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")

    st.markdown("### 📍 주소 검색")
    address_iframe()
    selected_address = st.text_input("검색한 주소를 입력하세요")
    detail_address = st.text_input("상세주소 (동/호수 등)")

    install_date = st.date_input("시공 희망일")

    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드", ["간편측정", "실제측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수", min_value=1, step=1)
        area_type = st.selectbox("시공 범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc(pyeong, area_type, expand_type)
            st.success(f"필요 매트: {total_mats}장")

    else:
        cnt = st.number_input("측정 구역 수", min_value=1, step=1)
        measurements = []
        for i in range(cnt):
            w = st.number_input(f"{i+1}번 구역 가로(cm)", min_value=1)
            h = st.number_input(f"{i+1}번 구역 세로(cm)", min_value=1)
            measurements.append((w, h))

        if st.button("계산하기"):
            total_mats = sum(math.ceil(w/80)*math.ceil(h/80) for w, h in measurements)
            st.success(f"정밀 계산된 매트 수: {total_mats}장")

    # ---------------------- 견적 출력 ----------------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        material_cost = total_mats * 40000
        work_cost = int(material_cost * 0.165)
        final_cost = material_cost + work_cost

        ### 견적서 영역 (인쇄될 부분)
        with st.container():
            st.markdown("<div id='printArea'>", unsafe_allow_html=True)
            st.write(f"**고객명:** {customer_name}")
            st.write(f"**연락처:** {customer_phone}")
            st.write(f"**주소:** {selected_address} {detail_address}")
            st.write(f"**희망 시공일:** {install_date}")

            st.write("---")
            st.write(f"총 매트 수량: **{total_mats}장**")
            st.write(f"재료비: **{material_cost:,}원**")
            st.write(f"시공비: **{work_cost:,}원**")
            st.write(f"최종 견적(VAT 포함): **{final_cost:,}원**")
            st.markdown("</div>", unsafe_allow_html=True)

        # 인쇄 버튼
        st.markdown(
            """
            <button onclick="printJS({ printable: 'printArea', type: 'html' })"
                    style="padding:8px 15px; background:#222; color:white; border:none; border-radius:5px;">
                🖨 인쇄하기
            </button>

            <script src="https://printjs-4de6.kxcdn.com/print.min.js"></script>
            """,
            unsafe_allow_html=True
        )


# --------------------------------------------------------
# 실행부
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()
