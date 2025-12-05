import streamlit as st
import math
import base64
from datetime import datetime

# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="견적프로그램",
    layout="centered",
)

ISOL_BLUE = "#2A7DE1"
LIGHT_BG = "#F5F9FF"

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
            <div style='text-align:center; margin-bottom:5px;'>
                <img src='data:image/png;base64,{logo}' width='130'>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except:
        st.error("⚠ isollogo.png 파일이 없습니다.")


def show_watermark():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style='position: fixed; bottom: 20px; right: 20px;
                opacity: 0.06; z-index: 999;'>
                <img src='data:image/png;base64,{logo}' width='160'>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except:
        pass


# --------------------------------------------------------
# 면적 → 장수 계산
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

    mats = int(mats * 1.10)  # +10%

    return max(mats, 0)


# --------------------------------------------------------
# 로그인
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown(f"<h2 style='text-align:center; color:{ISOL_BLUE};'>견적프로그램</h2>", unsafe_allow_html=True)

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("로그인 정보가 올바르지 않습니다.")


# --------------------------------------------------------
# 각 사이즈별 자동 가격 산출 (면적 비례 + 500원 반올림)
# --------------------------------------------------------
def calc_price_by_size(base_price, base_side_mm, target_side_mm):
    base_area = (base_side_mm / 10) ** 2
    target_area = (target_side_mm / 10) ** 2

    scaled_price = base_price * (target_area / base_area)

    # 500원 단위 반올림
    return int(round(scaled_price / 500) * 500)


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

    # 800×800 = 80cm 기준 면적
    base_area = mats_800 * (80 ** 2)

    mats = mats_from_area(base_area, mat_side_cm)

    if expand_type == "비확장형" and mat_side_cm == 80:
        mats -= 8  # 기존 규칙 유지 (800×800 전용)

    return max(mats, 0)


# --------------------------------------------------------
# 메인 계산 화면
# --------------------------------------------------------
def calculator():
    show_logo_top()
    show_watermark()

    st.markdown(f"<h1 style='text-align:center; color:{ISOL_BLUE};'>견적프로그램</h1>", unsafe_allow_html=True)

    st.subheader("🧾 고객 정보")
    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")
    address = st.text_input("주소")
    detail = st.text_input("상세주소")
    install_date = st.date_input("시공 희망일")

    # -----------------------------------
    # 재질 선택
    # -----------------------------------
    st.subheader("📌 매트 재질 선택")
    material_type = st.selectbox("재질", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])

    base_price_map = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000,
    }
    base_price = base_price_map[material_type]

    # -----------------------------------
    # 사이즈 선택
    # -----------------------------------
    st.subheader("📌 매트 크기 선택")
    mat_size_str = st.selectbox("사이즈", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])

    side_mm = int(mat_size_str.split("×")[0])
    mat_side_cm = side_mm / 10

    # 자동 가격 산출
    material_unit_price = calc_price_by_size(base_price, 800, side_mm)

    # 시공비 계산
    front = side_mm // 100
    work_cost_unit = front * side_mm

    # -----------------------------------
    # 계산모드
    # -----------------------------------
    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드", ["간편측정", "실측측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수", min_value=1)
        area = st.selectbox("범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc_with_size(pyeong, area, expand, mat_side_cm)
            st.success(f"총 필요 매트 수량: {total_mats} 장")

    else:
        st.subheader("📏 실측 입력")
        zones = ["거실", "복도", "아일랜드", "주방", "안방", "아이방1", "아이방2", "아이방3", "알파룸"]
        total_area = 0

        for z in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{z} 가로(cm)", min_value=0.0, key=f"{z}_w")
            h = col2.number_input(f"{z} 세로(cm)", min_value=0.0, key=f"{z}_h")
            if w > 0 and h > 0:
                total_area += w * h

        if st.button("계산하기"):
            total_mats = mats_from_area(total_area, mat_side_cm)
            st.success(f"총 필요 매트 수량: {total_mats} 장")

    # -----------------------------------
    # 견적 출력
    # -----------------------------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        material_cost = material_unit_price * total_mats
        work_cost = work_cost_unit * total_mats
        total_price = int((material_cost + work_cost) * 1.10)

        st.markdown(
            f"""
            <div style="
                background:{LIGHT_BG};
                padding:20px; border-radius:10px;
                border:1px solid #DCE6F5;">
                <h3 style='color:{ISOL_BLUE}; text-align:center;'>견적서</h3>

                <b>■ 고객 정보</b><br>
                고객명: {customer_name}<br>
                연락처: {customer_phone}<br>
                주소: {address} {detail}<br>
                시공 희망일: {install_date}<br><br>

                <b>■ 시공 내용</b><br>
                매트 재질: {material_type}<br>
                매트 크기: {mat_size_str}<br>
                필요 매트 수량: {total_mats} 장<br><br>

                <b>■ 비용 내역</b><br>
                재료비: {material_cost:,} 원<br>
                시공비: {work_cost:,} 원<br>
                <b>최종 견적(VAT 포함): {total_price:,} 원</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()