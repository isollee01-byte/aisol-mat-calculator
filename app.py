import streamlit as st
import math
import base64
from datetime import datetime
from urllib.parse import urlencode

st.set_page_config(page_title="매트 견적 시스템", layout="centered")

# --------------------------------------------------------
# 로고 Base64
# --------------------------------------------------------
def load_logo_base64():
    try:
        with open("isollogo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

LOGO_B64 = load_logo_base64()


# --------------------------------------------------------
# 로그인
# --------------------------------------------------------
def login():
    st.markdown("<h2 style='text-align:center;'>아이솔 매트 견적 시스템</h2>", unsafe_allow_html=True)
    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol2025" and pw == "isol202512!":
            st.session_state["login"] = True
            st.experimental_rerun()
        else:
            st.error("로그인 정보가 올바르지 않습니다.")


# --------------------------------------------------------
# 800×800 기준 계수 → 면적 기반 환산용
# --------------------------------------------------------
def mat_area_m2(size_str: str) -> float:
    """'800×800' → 0.64㎡"""
    w_mm, h_mm = size_str.split("×")
    w_m = int(w_mm) / 1000
    h_m = int(h_mm) / 1000
    return w_m * h_m


def mat_side_cm(size_str: str) -> float:
    """'800×800' → 80(cm)"""
    w_mm = int(size_str.split("×")[0])
    return w_mm / 10.0


# --------------------------------------------------------
# 비확장형 감산 (면적 기준 자동계산)
# 800×800 기준 8장 → 5.12㎡ 감산을 모든 사이즈에 자동 환산
# --------------------------------------------------------
def non_expand_deduction(size_str: str) -> int:
    base_reduction_area = 0.64 * 8  # 800×800 8장 = 5.12㎡
    area_per_mat = mat_area_m2(size_str)
    if area_per_mat <= 0:
        return 0
    deduction = base_reduction_area / area_per_mat
    return max(int(round(deduction)), 0)


# --------------------------------------------------------
# 면적 → 장수 (간편모드용, 10% 여유 포함)
# --------------------------------------------------------
def mats_from_area_cm2(total_area_cm2: float, mat_side_cm_val: float) -> int:
    if total_area_cm2 <= 0 or mat_side_cm_val <= 0:
        return 0

    mat_area = mat_side_cm_val * mat_side_cm_val  # cm²
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

    mats = int(mats * 1.10)  # +10% 여유
    return max(mats, 0)


# --------------------------------------------------------
# 간편측정 모드 (평수 기반)
#  - 800×800 기준 계수로 면적을 만들고,
#  - 선택한 매트 크기에 맞게 다시 장수 환산
# --------------------------------------------------------
def simple_mode_calc_with_size(pyeong: float, area_type: str, extend_type: str, size_str: str) -> int:
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0,
    }
    mats_800_raw = pyeong * factor_800[area_type]   # 800×800 기준 예상 장수 (여기서는 면적용 초벌값)

    base_mat_side_800_cm = 80.0  # 800mm = 80cm
    base_area_cm2 = mats_800_raw * (base_mat_side_800_cm ** 2)  # cm²

    # 선택한 매트 크기에 따른 실제 장수
    side_cm = mat_side_cm(size_str)
    mats = mats_from_area_cm2(base_area_cm2, side_cm)

    # 비확장형이면 감산
    if extend_type == "비확장형":
        mats -= non_expand_deduction(size_str)

    return max(mats, 0)


# --------------------------------------------------------
# 실측모드 계산 (공식 2번: (가로-30)/(매트 한변), (세로-30)/(매트 한변))
#  - 구역별로 row/col 계산 후 합산
#  - 마지막에 +10% 여유
#  - 실측은 확장/비확장 감산 없음
# --------------------------------------------------------
def precision_mode_calc(measures_cm, size_str: str) -> int:
    side_cm = mat_side_cm(size_str)
    if side_cm <= 0:
        return 0

    total_raw = 0
    for w_cm, h_cm in measures_cm:
        if w_cm <= 0 or h_cm <= 0:
            continue

        eff_w = max(w_cm - 30, 0)  # 30cm 여유 반영
        eff_h = max(h_cm - 30, 0)

        row = math.ceil(eff_w / side_cm) if eff_w > 0 else 0
        col = math.ceil(eff_h / side_cm) if eff_h > 0 else 0

        total_raw += row * col

    mats = int(total_raw * 1.10)  # +10% 여유
    return max(mats, 0)


# --------------------------------------------------------
# 메인 페이지
# --------------------------------------------------------
def main():
    st.markdown("<h1 style='text-align:center;'>매트 견적 시스템</h1>", unsafe_allow_html=True)

    # 고객 정보
    st.subheader("🧾 고객 정보")
    customer = st.text_input("고객명")
    phone = st.text_input("연락처")
    address = st.text_input("주소")
    date = st.date_input("시공 희망일")

    # 공통 옵션
    st.subheader("📌 매트 옵션")
    size = st.selectbox("매트 크기 선택", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])
    material = st.selectbox("매트 재질", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])

    material_price = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000,
    }

    # 계산 모드
    st.subheader("📌 계산 모드")
    mode = st.selectbox("계산 방식", ["간편측정", "실측측정"])

    total_mats = 0
    extend_type = "-"

    # ---------------- 간편측정 ----------------
    if mode == "간편측정":
        extend_type = st.selectbox("확장 여부", ["확장형", "비확장형"])
        pyeong = st.number_input("평수 입력", min_value=1.0, step=1.0)
        area_type = st.selectbox(
            "시공 범위",
            ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"],
        )

        if st.button("계산하기", key="simple_calc"):
            total_mats = simple_mode_calc_with_size(pyeong, area_type, extend_type, size)
            st.success(f"총 필요 매트 수량: {total_mats} 장")

    # ---------------- 실측측정 ----------------
    else:
        st.info("실측모드에서는 확장/비확장 개념 없이, 실제 치수 기준으로 계산합니다.")
        zones = ["거실", "복도", "아일랜드", "주방", "안방", "아이방1", "아이방2", "아이방3", "알파룸"]

        measures = []
        st.subheader("📏 실측 입력 (cm 단위, 필요한 구역만 입력)")

        for zone in zones:
            st.write(f"### 🏷 {zone}")
            c1, c2 = st.columns(2)
            w = c1.number_input(f"{zone} 가로(cm)", min_value=0.0, step=1.0, key=f"{zone}_w")
            h = c2.number_input(f"{zone} 세로(cm)", min_value=0.0, step=1.0, key=f"{zone}_h")
            if w > 0 and h > 0:
                measures.append((w, h))

        if st.button("계산하기", key="precision_calc"):
            total_mats = precision_mode_calc(measures, size)
            st.success(f"실측 기반 총 필요 매트 수량: {total_mats} 장")

    # ---------------- 견적 결과 & 인쇄 ----------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        mat_cost = total_mats * material_price[material]

        side_mm = int(size.split("×")[0])
        front_number = side_mm // 100
        labor_per_mat = front_number * side_mm          # 600×600 → 6×600=3600
        labor_cost = total_mats * labor_per_mat

        default_final = mat_cost + labor_cost
        final_price = st.number_input(
            "최종 견적금액 (수정 가능, VAT 포함 금액 입력 권장)",
            value=int(default_final),
            step=1000
        )

        st.write(f"- 매트 수량: **{total_mats} 장**")
        st.write(f"- 재료비: **{mat_cost:,} 원**")
        st.write(f"- 시공비: **{labor_cost:,} 원**")
        st.write(f"- 계산 기준 총액(수정 전): **{default_final:,} 원**")
        st.write(f"- 최종 견적(수정 후): **{final_price:,} 원**")

        if st.button("견적서 인쇄"):
            # 인쇄 페이지로 넘길 파라미터 구성
            params = {
                "customer": customer,
                "phone": phone,
                "address": address,
                "date": str(date),
                "material": material,
                "size": size,
                "extend": extend_type if mode == "간편측정" else "실측",
                "mats": str(total_mats),
                "mat_cost": str(mat_cost),
                "labor_cost": str(labor_cost),
                "final_cost": str(final_price),
            }
            query = urlencode(params, doseq=True)
            st.markdown(
                f"""
                <script>
                    window.open('/print?{query}', '_blank');
                </script>
                """,
                unsafe_allow_html=True,
            )


# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
else:
    main()