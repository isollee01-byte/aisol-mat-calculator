import streamlit as st
import math
import base64
from datetime import datetime


# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="매트 견적프로그램",
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
            f"<div style='text-align:center; margin-bottom:10px;'>"
            f"<img src='data:image/png;base64,{logo}' width='130'></div>",
            unsafe_allow_html=True,
        )
    except:
        st.error("⚠ isollogo.png 파일이 없습니다. app.py와 같은 폴더에 넣어주세요.")


def show_watermark():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style='position: fixed; bottom: 25px; right: 25px;
                opacity: 0.08; z-index: 999;'>
                <img src='data:image/png;base64,{logo}' width='160'>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except:
        pass


# --------------------------------------------------------
# 면적 기반 장수 계산 (간편측정용)
# --------------------------------------------------------
def mats_from_area(total_area_cm2: float, mat_side_cm: float) -> int:
    if total_area_cm2 <= 0 or mat_side_cm <= 0:
        return 0

    mat_area = mat_side_cm * mat_side_cm
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

    mats = int(mats * 1.10)  # +10% 여유 추가

    return max(mats, 0)


# --------------------------------------------------------
# 비확장형 감산 (면적 비례 방식)
# --------------------------------------------------------
def non_expand_deduction(mat_side_cm):
    base_area_800 = 0.64  # 80cm × 80cm = 0.64㎡
    base_ded_area = base_area_800 * 8  # 5.12㎡ 감산

    mat_area_m2 = (mat_side_cm / 100) * (mat_side_cm / 100)

    if mat_area_m2 <= 0:
        return 0

    ded_mats = base_ded_area / mat_area_m2
    return max(int(round(ded_mats)), 0)


# --------------------------------------------------------
# 로그인 화면
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown("<h2 style='text-align:center;'>매트 견적프로그램 로그인</h2>", unsafe_allow_html=True)

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol2025" and pw == "isol202512!":
            st.session_state["login"] = True
            st.experimental_rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


# --------------------------------------------------------
# 간편측정
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
        mats -= non_expand_deduction(mat_side_cm)

    return max(mats, 0)


# --------------------------------------------------------
# 실측측정 (공식 2번)
# --------------------------------------------------------
def precision_calc(measures, mat_side_cm):
    total = 0

    for w, h in measures:
        eff_w = max(w - 30, 0)
        eff_h = max(h - 30, 0)

        if eff_w <= 0 or eff_h <= 0:
            continue

        row = math.ceil(eff_w / mat_side_cm)
        col = math.ceil(eff_h / mat_side_cm)

        total += row * col

    return total


# --------------------------------------------------------
# 메인 견적 시스템
# --------------------------------------------------------
def calculator():
    show_logo_top()
    show_watermark()

    st.markdown("<h1 style='text-align:center; font-weight:700;'>매트 견적프로그램</h1>", unsafe_allow_html=True)

    st.subheader("🧾 고객 정보")
    customer = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    addr_detail = st.text_input("상세 주소")
    install_date = st.date_input("시공 희망일")

    st.subheader("📌 재질 선택")
    material = st.selectbox("매트 재질", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])
    price_map = {"일반 TPU": 39000, "프리미엄 TPU": 42000, "패브릭 TPU": 50000}
    material_price = price_map[material]

    st.subheader("📌 매트 크기 선택")
    size_str = st.selectbox("크기", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])
    side_mm = int(size_str.split("×")[0])
    mat_side_cm = side_mm / 10

    front_num = side_mm // 100
    work_cost_per_mat = front_num * side_mm

    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드", ["간편측정", "실제측정"])

    total_mats = 0

    # 간편측정 ----------------------
    if mode == "간편측정":
        pyeong = st.number_input("평수", min_value=1)
        area_type = st.selectbox("범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm)
            st.success(f"총 필요 매트: {total_mats}장")

    # 실측측정 -----------------------
    else:
        st.subheader("📏 실측 입력")
        zones = ["거실", "복도", "아일랜드", "주방", "안방", "아이방1", "아이방2", "아이방3", "알파룸"]

        measures = []
        for zone in zones:
            st.write(f"### 🏷 {zone}")
            c1, c2 = st.columns(2)
            w = c1.number_input(f"{zone} 가로(cm)", min_value=0.0, key=f"{zone}_w")
            h = c2.number_input(f"{zone} 세로(cm)", min_value=0.0, key=f"{zone}_h")

            if w > 0 and h > 0:
                measures.append((w, h))

        if st.button("계산하기"):
            total_mats = precision_calc(measures, mat_side_cm)
            st.success(f"실측 총 매트: {total_mats}장")

    # 견적 결과 -----------------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        material_cost = total_mats * material_price
        work_cost = total_mats * work_cost_per_mat
        total_price = int((material_cost + work_cost) * 1.10)

        st.write(f"매트 수량: **{total_mats} 장**")
        st.write(f"재료비: **{material_cost:,} 원**")
        st.write(f"시공비: **{work_cost:,} 원**")
        st.write(f"최종 견적(VAT 포함): **{total_price:,} 원**")

        st.markdown("<div id='printArea'>", unsafe_allow_html=True)
        st.write(f"**고객명:** {customer}")
        st.write(f"**연락처:** {phone}")
        st.write(f"**주소:** {addr} {addr_detail}")
        st.write(f"**시공일:** {install_date}")
        st.write(f"**매트:** {material} / {size_str}")
        st.markdown("---")
        st.write(f"총 {total_mats}장 / 재료비 {material_cost:,} / 시공비 {work_cost:,} / 총액 {total_price:,}")
        st.markdown("</div>", unsafe_allow_html=True)

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
            unsafe_allow_html=True,
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