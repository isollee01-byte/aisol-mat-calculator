import streamlit as st
import math
import base64
from datetime import datetime

# -----------------------------------------------
# 기본 설정
# -----------------------------------------------
st.set_page_config(page_title="매트 견적프로그램", layout="centered")

# -----------------------------------------------
# 로고 표시
# -----------------------------------------------
def get_base64(bin_file):
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo_top():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"<div style='text-align:center; margin-bottom:15px;'><img src='data:image/png;base64,{logo}' width='130'></div>",
            unsafe_allow_html=True,
        )
    except:
        st.warning("로고 파일이 없습니다.")

# -----------------------------------------------
# 장수 계산 함수
# -----------------------------------------------
def mats_from_area(total_area_cm2: float, mat_side_cm: float) -> int:
    if total_area_cm2 <= 0: return 0

    mat_area = mat_side_cm * mat_side_cm
    raw = total_area_cm2 / mat_area

    frac = raw - int(raw)
    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    mats = int(mats * 1.10)  # 여유분 10%
    return max(mats, 0)

# -----------------------------------------------
# 500원 단위 반올림
# -----------------------------------------------
def round_500(x):
    return int(round(x / 500) * 500)

# -----------------------------------------------
# 800×800 기준 단가
# -----------------------------------------------
base_price_map = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}

# -----------------------------------------------
# 간편측정 모드(평수)
# -----------------------------------------------
def simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm):
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2,
    }

    mats_800 = pyeong * factor_800[area_type]
    base_area = (80 ** 2)
    total_area = mats_800 * base_area
    
    mats = mats_from_area(total_area, mat_side_cm)

    if expand_type == "비확장형":
        mats -= 8

    return max(mats, 0)

# -----------------------------------------------
# 로그인 화면
# -----------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown("<h2 style='text-align:center;'>매트 견적프로그램 로그인</h2>", unsafe_allow_html=True)

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# -----------------------------------------------
# 메인 계산 페이지
# -----------------------------------------------
def calculator():
    show_logo_top()
    st.markdown("<h1 style='text-align:center;'>매트 견적프로그램</h1>", unsafe_allow_html=True)

    # ---------------- 고객 정보 ----------------
    st.subheader("🧾 고객 정보")
    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")
    selected_address = st.text_input("주소 입력")
    detail_address = st.text_input("상세 주소 입력")
    install_date = st.date_input("시공 희망일")

    # ---------------- 재질 선택 ----------------
    st.subheader("📌 매트 재질 선택")
    material_type = st.selectbox(
        "원단 재질 선택",
        ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"]
    )

    # ---------------- 크기 선택 ----------------
    st.subheader("📌 매트 크기 선택")
    mat_size_str = st.selectbox("매트 크기 선택",
                                ["600×600","700×700","800×800","1000×1000","1200×1200"])

    side_mm = int(mat_size_str.split("×")[0])
    mat_side_cm = side_mm / 10

    # 시공비 공식
    front_number = side_mm // 100
    work_cost_per_mat = front_number * side_mm

    # 단가 = 면적비 × 기본단가 → 500원 반올림
    area = mat_side_cm * mat_side_cm
    base_area = 80 * 80
    ratio = area / base_area
    material_unit_price = round_500(base_price_map[material_type] * ratio)

    st.info(f"선택 사이즈 단가: **{material_unit_price:,}원 / 장**\n시공비: **{work_cost_per_mat:,}원 / 장**")

    # ---------------- 계산 모드 ----------------
    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox("범위 선택", 
                                 ["거실","거실+복도","거실+복도+아이방1","거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형","비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm)
            st.success(f"총 필요 매트 수량: {total_mats}장")

    else:
        st.subheader("📏 실측 입력")
        zones = ["거실","복도","아일랜드","주방","안방","아이방1","아이방2","아이방3","알파룸"]
        total_area = 0

        for zone in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{zone} 가로(cm)", min_value=0.0, key=f"{zone}_w")
            h = col2.number_input(f"{zone} 세로(cm)", min_value=0.0, key=f"{zone}_h")
            if w > 0 and h > 0:
                total_area += w * h

        if st.button("계산하기"):
            total_mats = mats_from_area(total_area, mat_side_cm)
            st.success(f"총 필요 매트 수량: {total_mats}장")

    # ---------------- 견적서 출력 ----------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        material_cost = total_mats * material_unit_price
        work_cost = total_mats * work_cost_per_mat
        total_price = int((material_cost + work_cost) * 1.10)

        # 💎 프리미엄 견적서 디자인
        st.markdown(
            f"""
            <div style="
                background:#F8FAFC; padding:25px; border-radius:12px;
                border:1.5px solid #E2E8F0;">
                <h2 style="text-align:center; color:#007ACC;">견적서</h2>

                <h4 style="color:#1F2937;">■ 고객 정보</h4>
                고객명: {customer_name}<br>
                연락처: {customer_phone}<br>
                주소: {selected_address} {detail_address}<br>
                시공 희망일: {install_date}<br><br>

                <h4 style="color:#1F2937;">■ 시공 내용</h4>
                매트 재질: {material_type}<br>
                매트 크기: {mat_size_str}<br>
                필요 매트 수량: {total_mats} 장<br><br>

                <h4 style="color:#1F2937;">■ 비용 내역</h4>
                재료비: {material_cost:,} 원<br>
                시공비: {work_cost:,} 원<br>
                <b>최종 견적 (VAT 포함): {total_price:,} 원</b><br>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------
# 실행
# -----------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()