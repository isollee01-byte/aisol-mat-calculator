import streamlit as st
import math
from datetime import datetime

# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="매트 견적프로그램",
    layout="centered",
)

# --------------------------------------------------------
# 상단 로고 표시 (유지)
# --------------------------------------------------------
def show_logo_top():
    try:
        with open("isollogo.png", "rb") as f:
            import base64
            logo = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style='text-align:center; margin-bottom:10px;'>
                <img src='data:image/png;base64,{logo}' width='130'>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except:
        pass


# --------------------------------------------------------
# 공통 계산 함수
# --------------------------------------------------------
def mats_from_area(total_area_cm2: float, mat_side_cm: float) -> int:
    if total_area_cm2 <= 0 or mat_side_cm <= 0:
        return 0

    mat_area = mat_side_cm * mat_side_cm
    raw = total_area_cm2 / mat_area

    frac = raw - int(raw)
    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    mats = int(mats * 1.10)
    return max(mats, 0)


# --------------------------------------------------------
# 로그인 화면
# --------------------------------------------------------
def login_screen():
    show_logo_top()

    st.markdown(
        """
        <h2 style='text-align:center;
                   margin-top:-10px;
                   margin-bottom:25px;
                   font-weight:700;'>
            매트 견적프로그램
        </h2>
        """,
        unsafe_allow_html=True
    )

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


# --------------------------------------------------------
# 간편측정 계산
# --------------------------------------------------------
def simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm):
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2,
    }
    mats_800 = pyeong * factor_800[area_type]
    base_area = mats_800 * (80 ** 2)
    mats = mats_from_area(base_area, mat_side_cm)

    if expand_type == "비확장형":
        mats -= 8

    return max(mats, 0)


# --------------------------------------------------------
# 메인 견적 시스템
# --------------------------------------------------------
def calculator():
    show_logo_top()

    st.markdown("<h1 style='text-align:center;'>매트 견적프로그램</h1>", unsafe_allow_html=True)

    # -------------------- 고객 정보 --------------------
    st.subheader("🧾 고객 정보")
    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")
    selected_address = st.text_input("주소 입력")
    detail_address = st.text_input("상세 주소 입력")
    install_date = st.date_input("시공 희망일")

    # -------------------- 매트 재질 --------------------
    st.subheader("📌 매트 재질 선택")

    material_type = st.selectbox(
        "원단 재질",
        ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"],
    )

    material_price_map = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000,
    }
    material_unit_price = material_price_map[material_type]

    # -------------------- 매트 크기 --------------------
    st.subheader("📌 매트 크기 선택")

    mat_size_str = st.selectbox(
        "매트 크기",
        ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"],
    )

    side_mm = int(mat_size_str.split("×")[0])
    mat_side_cm = side_mm / 10

    front_number = side_mm // 100
    work_cost_per_mat = front_number * side_mm

    # -------------------- 계산 모드 --------------------
    st.subheader("📌 계산 모드 선택")

    mode = st.selectbox("계산 방식 선택", ["간편측정", "실제측정"])
    total_mats = 0

    # -------------------- 간편측정 --------------------
    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox("범위 선택",
                                 ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc_with_size(
                pyeong, area_type, expand_type, mat_side_cm
            )
            st.success(f"총 필요 매트 수량: {total_mats}장")

    # -------------------- 실제측정 --------------------
    else:
        st.subheader("📏 실측 측정")

        zones = ["거실", "복도", "아일랜드", "주방", "안방",
                 "아이방1", "아이방2", "아이방3", "알파룸"]

        total_area_cm2 = 0

        for zone in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{zone} 가로(cm)", min_value=0.0, key=f"{zone}_w")
            h = col2.number_input(f"{zone} 세로(cm)", min_value=0.0, key=f"{zone}_h")

            if w > 0 and h > 0:
                total_area_cm2 += (w * h)

        if st.button("실측 계산하기"):
            total_mats = mats_from_area(total_area_cm2, mat_side_cm)
            st.success(f"총 매트 수량: {total_mats}장")

    # -------------------- 견적 결과 --------------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        material_cost = total_mats * material_unit_price
        work_cost = total_mats * work_cost_per_mat
        total_price = int((material_cost + work_cost) * 1.10)

        st.markdown(
            f"""
            <div style='padding:20px; background:#f5f5f5; border-radius:8px;'>
                <h3 style='text-align:center;'>견적서</h3>

                <b>■ 고객 정보</b><br>
                고객명: {customer_name}<br>
                연락처: {customer_phone}<br>
                주소: {selected_address} {detail_address}<br>
                시공 희망일: {install_date}<br><br>

                <b>■ 시공 내용</b><br>
                매트 재질: {material_type}<br>
                매트 크기: {mat_size_str}<br>
                필요 매트 수량: {total_mats:,} 장<br><br>

                <b>■ 비용 내역</b><br>
                재료비: {material_cost:,} 원<br>
                시공비: {work_cost:,} 원<br>
                <b>최종 견적(VAT 포함): {total_price:,} 원</b>
            </div>
            """,
            unsafe_allow_html=True
        )


# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
    st.stop()
else:
    calculator()