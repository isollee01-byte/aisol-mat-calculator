import streamlit as st
import math
import base64
from datetime import datetime

# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="아이솔(ISOL) 매트 견적프로그램",
    layout="centered",
)

# --------------------------------------------------------
# 로고 / 워터마크 처리
# --------------------------------------------------------
def get_base64(bin_file):
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo_top():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:10px;">
                <img src="data:image/png;base64,{logo}" width="130">
            </div>
            """,
            unsafe_allow_html=True
        )
    except:
        st.error("⚠️ isollogo.png 파일이 없습니다.")

def show_watermark():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="
                position: fixed;
                bottom: 25px;
                right: 25px;
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
# 로그인 화면
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown(
        "<h2 style='text-align:center;'>아이솔(ISOL) 견적 시스템 로그인</h2>",
        unsafe_allow_html=True
    )

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol2025" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()  # ← 즉시 페이지 전환
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


# --------------------------------------------------------
# 간편 계산 로직
# --------------------------------------------------------
def simple_mode_calc(pyeong, area_type, expand_type):
    factor = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2
    }

    mats = pyeong * factor[area_type]

    # 손실 반영 규칙
    if mats - int(mats) <= 0.3:
        mats = int(mats)
    elif mats - int(mats) >= 0.6:
        mats = int(mats) + 1
    else:
        mats = math.ceil(mats)

    mats = int(mats * 1.10)  # +10%

    if expand_type == "비확장형":
        mats -= 8

    return max(mats, 0)


# --------------------------------------------------------
# 메인 견적 계산기
# --------------------------------------------------------
def calculator():
    show_logo_top()
    show_watermark()

    st.markdown("<h1 style='text-align:center;'>아이솔(ISOL) 매트 견적프로그램</h1>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # 고객 정보 입력
    # ----------------------------------------------------
    st.subheader("🧾 고객 정보")

    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")
    selected_address = st.text_input("주소 입력")
    detail_address = st.text_input("상세 주소")
    install_date = st.date_input("시공 희망일")

    # ----------------------------------------------------
    # TPU 재질 선택
    # ----------------------------------------------------
    st.subheader("📌 재질 선택")

    material_type = st.selectbox(
        "매트 재질 선택",
        ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"]
    )

    price_map = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000
    }

    unit_price = price_map[material_type]

    # ----------------------------------------------------
    # 계산 모드 선택
    # ----------------------------------------------------
    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    # ----------------------------------------------------
    # 간편측정 모드
    # ----------------------------------------------------
    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox(
            "범위 선택",
            ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"]
        )
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc(pyeong, area_type, expand_type)
            st.success(f"총 필요 매트 수량: {total_mats}장")

    # ----------------------------------------------------
    # 실제측정 모드 (고정 구역 입력)
    # ----------------------------------------------------
    else:
        st.subheader("📏 실측 입력 (필요한 구역만 입력하세요)")

        zones = [
            "거실", "복도", "아일랜드", "주방",
            "안방", "아이방1", "아이방2", "아이방3", "알파룸"
        ]

        measurements = []

        for zone in zones:
            st.write(f"### 🏷 {zone}")
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{zone} 가로(cm)", min_value=0, key=f"{zone}_w")
            h = col2.number_input(f"{zone} 세로(cm)", min_value=0, key=f"{zone}_h")

            if w > 0 and h > 0:
                measurements.append((w, h))

        if st.button("계산하기"):
            total_mats = sum(
                math.ceil(w / 80) * math.ceil(h / 80)
                for w, h in measurements
            )
            st.success(f"총 실측 매트 수량: {total_mats}장")

    # ----------------------------------------------------
    # 견적 결과 출력
    # ----------------------------------------------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        # 재료비 계산
        material_cost = total_mats * unit_price

        # 시공비 (고정식)
        work_cost = total_mats * 6400

        # VAT 포함 최종가
        total_price = int((material_cost + work_cost) * 1.10)

        # 인쇄 영역
        st.markdown("<div id='printArea'>", unsafe_allow_html=True)

        st.write(f"**고객명:** {customer_name}")
        st.write(f"**연락처:** {customer_phone}")
        st.write(f"**주소:** {selected_address} {detail_address}")
        st.write(f"**재질:** {material_type}")
        st.write(f"**시공 희망일:** {install_date}")
        st.write("---")
        st.write(f"매트 수량: **{total_mats} 장**")
        st.write(f"재료비: **{material_cost:,} 원**")
        st.write(f"시공비(장당 6,400원): **{work_cost:,} 원**")
        st.write(f"최종 견적(VAT 포함): **{total_price:,} 원**")

        st.markdown("</div>", unsafe_allow_html=True)

        # ------------------------------------------------
        # 인쇄 기능 (완전 정상 작동)
        # ------------------------------------------------
        st.markdown(
            """
            <script>
                function printPage() {
                    const printContents = document.getElementById('printArea').innerHTML;
                    const originalContents = document.body.innerHTML;

                    document.body.innerHTML = printContents;
                    window.print();
                    document.body.innerHTML = originalContents;
                    location.reload();
                }
            </script>

            <button onclick="printPage()"
                style="padding:10px 20px; background:black; color:white;
                       border:none; border-radius:6px; margin-top:12px; cursor:pointer;">
                🖨 인쇄하기
            </button>
            """,
            unsafe_allow_html=True
        )


# --------------------------------------------------------
# 실행 제어 (로그인 한 번 클릭 문제 해결!)
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if st.session_state["login"] is False:
    login_screen()
    st.stop()  # ← 반드시 필요! 로그인 후 즉시 페이지 전환
else:
    calculator()