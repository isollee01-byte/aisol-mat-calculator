import streamlit as st
import math
import base64
from datetime import date

# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="견적프로그램",
    layout="centered",
)


# --------------------------------------------------------
# 로고 표시
# --------------------------------------------------------
def get_base64(bin_file: str) -> str:
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()


def show_logo_top():
    """상단 로고 표시"""
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"<div style='text-align:center; margin:5px 0 10px 0;'>"
            f"<img src='data:image/png;base64,{logo}' width='130'></div>",
            unsafe_allow_html=True,
        )
    except Exception:
        st.error("⚠ isollogo.png 파일이 없습니다. app.py와 같은 폴더에 넣어주세요.")


# --------------------------------------------------------
# 장수 계산 (공통)
# --------------------------------------------------------
def mats_from_area(total_area_cm2: float, mat_side_cm: float) -> int:
    """
    total_area_cm2 : 전체 바닥 면적 (cm^2)
    mat_side_cm    : 매트 한 변 길이 (cm)  예) 60, 70, 80, 100, 120
    """
    if total_area_cm2 <= 0 or mat_side_cm <= 0:
        return 0

    mat_area = mat_side_cm * mat_side_cm  # 1장 면적 (cm^2)
    raw = total_area_cm2 / mat_area

    if raw <= 0:
        return 0

    frac = raw - int(raw)
    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    # +10% 여유
    mats = int(mats * 1.10)
    return max(mats, 0)


# --------------------------------------------------------
# 간편측정(평수) 계산
# --------------------------------------------------------
def simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm):
    # 800×800 기준 장수 계수
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0,
    }

    mats_800 = pyeong * factor_800[area_type]

    # 1장 = 80cm × 80cm 기준 면적으로 변환
    base_mat_side_800 = 80  # cm (800mm)
    base_area = mats_800 * (base_mat_side_800 ** 2)  # cm^2

    # 선택된 매트 크기에 맞춰 장수 재계산
    mats = mats_from_area(base_area, mat_side_cm)

    # 비확장형인 경우 800×800 기준 -8장을 적용하던 규칙을,
    # 여기서는 800×800일 때에만 -8장 적용
    if expand_type == "비확장형" and mat_side_cm == 80:
        mats -= 8

    return max(mats, 0)


# --------------------------------------------------------
# 로그인 화면
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown(
        "<h1 style='text-align:center; margin-top:5px;'>견적프로그램</h1>",
        unsafe_allow_html=True,
    )

    st.write("아이디와 비밀번호를 입력하세요.")

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("로그인 정보가 올바르지 않습니다.")


# --------------------------------------------------------
# 메인 견적 계산 화면
# --------------------------------------------------------
def calculator():
    show_logo_top()
    st.markdown("<h1 style='text-align:center;'>견적프로그램</h1>", unsafe_allow_html=True)

    # -----------------------------
    # 1. 고객 정보
    # -----------------------------
    st.subheader("🧾 고객 정보")
    name = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    detail_addr = st.text_input("상세주소")
    install_date = st.date_input("시공희망일", value=date.today())

    # -----------------------------
    # 2. 재질 선택 (가격은 화면에 노출 X)
    # -----------------------------
    st.subheader("📌 매트 재질 선택")
    material_type = st.selectbox(
        "원단 재질 선택",
        ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"],
    )

    # 800×800 기준 단가 (내부 계산용 / 화면 노출 X)
    base_price_800 = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000,
    }

    # -----------------------------
    # 3. 매트 크기 선택 (가격 노출 X)
    # -----------------------------
    st.subheader("📌 매트 크기 선택")
    mat_size = st.selectbox(
        "매트 크기 선택",
        ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"],
    )

    side_mm = int(mat_size.split("×")[0])
    mat_side_cm = side_mm / 10.0

    # -----------------------------
    # 4. 계산 모드 선택
    # -----------------------------
    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    # ---------------- 간편측정 ----------------
    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox(
            "범위 선택",
            ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"],
        )
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기", key="simple_calc"):
            total_mats = simple_mode_calc_with_size(
                pyeong, area_type, expand_type, mat_side_cm
            )
            st.success(f"필요 매트 수량: {total_mats}장")

    # ---------------- 실제측정 ----------------
    else:
        st.subheader("📏 실측 입력 (필요한 구역만 입력하세요)")
        zones = [
            "거실", "복도", "아일랜드", "주방",
            "안방", "아이방1", "아이방2", "아이방3", "알파룸",
        ]
        total_area = 0.0

        for zone in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{zone} 가로(cm)", min_value=0.0, key=f"{zone}_w")
            h = col2.number_input(f"{zone} 세로(cm)", min_value=0.0, key=f"{zone}_h")
            if w > 0 and h > 0:
                total_area += (w * h)

        if st.button("계산하기", key="precise_calc"):
            total_mats = mats_from_area(total_area, mat_side_cm)
            st.success(f"필요 매트 수량: {total_mats}장")

    # -----------------------------
    # 5. 견적서 (여기서만 가격 노출)
    # -----------------------------
    if total_mats > 0:
        st.subheader("📄 견적서")

        # 내부 가격 계산 (고객이 보는 화면에서는 오직 아래 블록에서만 노출)
        # 1) 재료비/장
        base_price = base_price_800[material_type]
        area_ratio = (side_mm * side_mm) / (800 * 800)
        raw_unit_price = base_price * area_ratio
        unit_price = int(round(raw_unit_price / 500.0) * 500)  # 500원 단위 반올림

        # 2) 시공비/장 (앞자리 × mm)
        front_num = side_mm // 100
        install_cost_per_mat = front_num * side_mm

        # 총액 계산
        material_cost = unit_price * total_mats
        install_cost = install_cost_per_mat * total_mats
        final_price = int((material_cost + install_cost) * 1.10)  # VAT 포함

        st.write("아래 내역은 고객에게 제시되는 최종 견적입니다.")

        st.markdown("---")
        st.markdown("**[고객 정보]**")
        st.write(f"- 고객명: {name}")
        st.write(f"- 연락처: {phone}")
        st.write(f"- 주소: {addr} {detail_addr}")
        st.write(f"- 시공희망일: {install_date}")

        st.markdown("**[시공 내용]**")
        st.write(f"- 매트 재질: {material_type}")
        st.write(f"- 매트 크기: {mat_size}")
        st.write(f"- 필요 매트 수량: {total_mats} 장")

        st.markdown("**[비용 내역]**")
        st.write(f"- 재료비: {material_cost:,} 원")
        st.write(f"- 시공비: {install_cost:,} 원")
        st.write(f"- **최종 견적 (VAT 포함)**: **{final_price:,} 원**")


# --------------------------------------------------------
# 실행 제어
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()