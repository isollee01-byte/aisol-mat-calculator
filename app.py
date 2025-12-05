import streamlit as st
import math
from datetime import datetime

# -------------------------
# 브랜드 컬러 세팅
# -------------------------
AISOL_MAIN = "#61A8C9"
AISOL_DARK = "#3A667A"
AISOL_LIGHT = "#E8F4FA"
BACKGROUND = "#F5F7FB"

st.set_page_config(
    page_title="아이솔(ISOL) 800 x 800 매트 견적프로그램",
    page_icon="🧩",
    layout="centered",
)

# -------------------------
# 전역 스타일
# -------------------------
st.markdown(
    f"""
    <style>
        body {{
            background-color: {BACKGROUND};
        }}
        .main-title {{
            color: {AISOL_MAIN};
            text-align: center;
            font-size: 30px;
            font-weight: 800;
            margin-bottom: 0px;
        }}
        .subtitle {{
            color: {AISOL_DARK};
            text-align: center;
            font-size: 16px;
            margin-top: 4px;
            margin-bottom: 20px;
        }}
        .aisol-card {{
            background-color: white;
            padding: 18px 20px;
            border-radius: 14px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            border: 1px solid #dde3ee;
            margin-bottom: 16px;
        }}
        .stButton>button {{
            background-color: {AISOL_MAIN} !important;
            color: white !important;
            border-radius: 8px !important;
            height: 42px;
            font-size: 16px;
            font-weight: 600;
            border: none;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='main-title'>아이솔(ISOL) 800 x 800 매트 견적프로그램</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>간편측정 · 실제측정 기반 프리미엄 매트 견적 산출</div>",
    unsafe_allow_html=True,
)

# -------------------------
# 상수 / 공통 함수
# -------------------------
MATERIAL_PRICE = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}
INSTALL_PRICE = 6400  # 장당 시공비

EASY_FACTORS = {
    "거실": 0.93,
    "거실 + 복도": 1.46,
    "거실 + 복도 + 아이방1": 1.67,
    "거실 + 복도 + 주방": 2.0,
}

ZONE_TYPES = [
    "거실",
    "복도",
    "아일랜드",
    "주방",
    "안방",
    "아이방1",
    "아이방2",
    "아이방3",
    "알파룸",
]


def band_round_ratio(value: float) -> int:
    """가로/세로 줄 수에 적용하는 0.3 / 0.6 규칙."""
    base = math.floor(value)
    frac = value - base
    if frac <= 0.3:
        return base
    elif frac >= 0.6:
        return base + 1
    else:
        return base


def calc_precision_mats(width_cm: float, height_cm: float) -> tuple[int, int, int]:
    """실제측정용: 가로/세로 cm → 줄 수(옵션C 규칙) 및 장수."""
    w_ratio = width_cm / 80.0
    h_ratio = height_cm / 80.0
    w_count = max(1, band_round_ratio(w_ratio))
    h_count = max(1, band_round_ratio(h_ratio))
    mats = w_count * h_count
    return w_count, h_count, mats


def calc_easy_mode(
    pyeong: float, area_type: str, is_extended: bool
) -> tuple[float, int, int]:
    """
    간편측정: 평수 × 계수 → 기본장수, 확장/비확장, +10%.
    return: (raw_float, rounded_base, final_mats_with_10pct)
    """
    coef = EASY_FACTORS[area_type]
    raw = pyeong * coef
    # 기본 장수 반올림 규칙 (단순화: 소수점 반올림)
    base = round(raw)

    if not is_extended:
        base = max(base - 8, 0)

    final_mats = math.ceil(base * 1.10)  # +10% 여유
    return raw, base, final_mats


def quote_from_mats(mats: int, material: str) -> tuple[int, int, int, int]:
    """장수 기준 견적 계산."""
    mat_cost = mats * MATERIAL_PRICE[material]
    install_cost = mats * INSTALL_PRICE
    subtotal = mat_cost + install_cost
    total = math.ceil(subtotal * 1.10)  # 부가세 10%
    return mat_cost, install_cost, subtotal, total


# -------------------------
# 1. 고객 정보 입력
# -------------------------
st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
st.markdown("### 🧾 고객 정보", unsafe_allow_html=True)
col_c1, col_c2 = st.columns(2)
with col_c1:
    customer_name = st.text_input("고객명")
with col_c2:
    customer_phone = st.text_input("연락처")

customer_address = st.text_input("주소 (선택 입력)")
desired_date = st.text_input("시공 희망일 (선택 입력 · 예: 2025-01-15)")

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 2. 공통 옵션 (계산 모드 / 재질)
# -------------------------
st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
mode = st.selectbox("계산 모드를 선택하세요", ["간편측정", "실제측정"])
material = st.selectbox("재질 선택", list(MATERIAL_PRICE.keys()))
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 3. 계산 로직
# -------------------------
print_html = None  # 프린트용 견적서 HTML (계산 후 생성)

# ===== 간편측정 모드 =====
if mode == "간편측정":
    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 📏 간편측정 (평수 기반)", unsafe_allow_html=True)

    pyeong = st.number_input("전용 면적 (평)", min_value=1.0, step=0.5)
    area_type = st.selectbox("시공 범위 선택", list(EASY_FACTORS.keys()))
    is_extended = st.radio(
        "확장형 여부", ["확장형", "비확장형"], horizontal=True, index=0
    )
    is_ext_bool = is_extended == "확장형"

    if st.button("간편측정 결과 계산하기"):
        raw, base, final_mats = calc_easy_mode(pyeong, area_type, is_ext_bool)
        mat_cost, install_cost, subtotal, total = quote_from_mats(final_mats, material)

        st.success(f"최종 필요 매트 수: {final_mats} 장")
        st.info(
            f"재료비: {mat_cost:,} 원 / 시공비: {install_cost:,} 원 / "
            f"합계(부가세 전): {subtotal:,} 원 / 최종 견적(VAT 포함): {total:,} 원"
        )

        # 프린트용 견적서 HTML 생성
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        print_html = f"""
        <div id="print-area" style="font-family: Arial, sans-serif; padding:24px;">
          <h2 style="color:{AISOL_MAIN}; margin-bottom:4px;">
            아이솔(ISOL) 800 x 800 매트 견적서
          </h2>
          <p style="color:#555; margin-top:0;">견적일자: {today}</p>
          <hr style="margin:12px 0 16px 0;">

          <h3 style="color:{AISOL_DARK};">고객 정보</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr>
              <td style="border:1px solid #ccc; padding:6px; width:20%;">고객명</td>
              <td style="border:1px solid #ccc; padding:6px;">{customer_name or ''}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">연락처</td>
              <td style="border:1px solid #ccc; padding:6px;">{customer_phone or ''}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">주소</td>
              <td style="border:1px solid #ccc; padding:6px;">{customer_address or ''}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">시공 희망일</td>
              <td style="border:1px solid #ccc; padding:6px;">{desired_date or ''}</td>
            </tr>
          </table>

          <h3 style="color:{AISOL_DARK};">견적 요약</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr>
              <td style="border:1px solid #ccc; padding:6px; width:20%;">계산 방식</td>
              <td style="border:1px solid #ccc; padding:6px;">간편측정 (평수 기반)</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">시공 범위</td>
              <td style="border:1px solid #ccc; padding:6px;">{area_type}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">확장형 여부</td>
              <td style="border:1px solid #ccc; padding:6px;">{is_extended}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">매트 재질</td>
              <td style="border:1px solid #ccc; padding:6px;">{material}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">최종 필요 매트 수</td>
              <td style="border:1px solid #ccc; padding:6px;">{final_mats} 장</td>
            </tr>
          </table>

          <h3 style="color:{AISOL_DARK};">금액 상세</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr>
              <td style="border:1px solid #ccc; padding:6px; width:20%;">재료비</td>
              <td style="border:1px solid #ccc; padding:6px;">{mat_cost:,} 원</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">시공비</td>
              <td style="border:1px solid #ccc; padding:6px;">{install_cost:,} 원</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">합계 (부가세 전)</td>
              <td style="border:1px solid #ccc; padding:6px;">{subtotal:,} 원</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px; font-weight:bold;">최종 견적 (VAT 포함)</td>
              <td style="border:1px solid #ccc; padding:6px; font-weight:bold;">{total:,} 원</td>
            </tr>
          </table>
        </div>
        """

    st.markdown("</div>", unsafe_allow_html=True)

# ===== 실제측정 모드 =====
elif mode == "실제측정":
    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 📐 실제측정 (실측 기반 구역별 입력)", unsafe_allow_html=True)
    st.markdown("각 구역을 선택하고 실측한 가로·세로(cm)를 입력해 주세요.", unsafe_allow_html=True)

    num_zones = st.number_input("입력할 구역 수", min_value=1, max_value=20, value=1)

    zones = []
    for i in range(int(num_zones)):
        st.markdown(f"**구역 {i+1}**", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.2, 1, 1])
        with c1:
            zone_type = st.selectbox(
                "구역 종류",
                ZONE_TYPES,
                key=f"zone_type_{i}",
            )
        with c2:
            w_cm = st.number_input(
                "가로(cm)",
                min_value=50.0,
                step=1.0,
                key=f"w_{i}",
            )
        with c3:
            h_cm = st.number_input(
                "세로(cm)",
                min_value=50.0,
                step=1.0,
                key=f"h_{i}",
            )
        zones.append({"type": zone_type, "w": w_cm, "h": h_cm})

    if st.button("실제측정 결과 계산하기"):
        total_mats = 0
        total_mat_cost = 0
        total_install_cost = 0
        total_subtotal = 0
        total_final = 0

        detail_rows_html = ""

        for i, z in enumerate(zones, start=1):
            w_count, h_count, mats = calc_precision_mats(z["w"], z["h"])
            mat_cost, install_cost, subtotal, total = quote_from_mats(mats, material)

            total_mats += mats
            total_mat_cost += mat_cost
            total_install_cost += install_cost
            total_subtotal += subtotal
            total_final += total

            st.write(
                f"- {z['type']} : 가로 {z['w']}cm / 세로 {z['h']}cm → "
                f"{w_count} x {h_count} = {mats}장"
            )

            detail_rows_html += f"""
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">{z['type']}</td>
              <td style="border:1px solid #ccc; padding:6px;">{z['w']} × {z['h']} cm</td>
              <td style="border:1px solid #ccc; padding:6px; text-align:right;">{w_count} × {h_count}</td>
              <td style="border:1px solid #ccc; padding:6px; text-align:right;">{mats}</td>
            </tr>
            """

        st.success(f"총 필요 매트 수: {total_mats} 장")
        st.info(
            f"재료비 합계: {total_mat_cost:,} 원 / 시공비 합계: {total_install_cost:,} 원 / "
            f"합계(부가세 전): {total_subtotal:,} 원 / 최종 견적(VAT 포함): {total_final:,} 원"
        )

        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        print_html = f"""
        <div id="print-area" style="font-family: Arial, sans-serif; padding:24px;">
          <h2 style="color:{AISOL_MAIN}; margin-bottom:4px;">
            아이솔(ISOL) 800 x 800 매트 견적서
          </h2>
          <p style="color:#555; margin-top:0;">견적일자: {today}</p>
          <hr style="margin:12px 0 16px 0;">

          <h3 style="color:{AISOL_DARK};">고객 정보</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr>
              <td style="border:1px solid #ccc; padding:6px; width:20%;">고객명</td>
              <td style="border:1px solid #ccc; padding:6px;">{customer_name or ''}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">연락처</td>
              <td style="border:1px solid #ccc; padding:6px;">{customer_phone or ''}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">주소</td>
              <td style="border:1px solid #ccc; padding:6px;">{customer_address or ''}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">시공 희망일</td>
              <td style="border:1px solid #ccc; padding:6px;">{desired_date or ''}</td>
            </tr>
          </table>

          <h3 style="color:{AISOL_DARK};">견적 요약</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr>
              <td style="border:1px solid #ccc; padding:6px; width:20%;">계산 방식</td>
              <td style="border:1px solid #ccc; padding:6px;">실제측정 (실측 기반)</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">매트 재질</td>
              <td style="border:1px solid #ccc; padding:6px;">{material}</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">총 필요 매트 수</td>
              <td style="border:1px solid #ccc; padding:6px;">{total_mats} 장</td>
            </tr>
          </table>

          <h3 style="color:{AISOL_DARK};">구역별 상세</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr style="background-color:{AISOL_LIGHT};">
              <th style="border:1px solid #ccc; padding:6px;">구역</th>
              <th style="border:1px solid #ccc; padding:6px;">실측 (cm)</th>
              <th style="border:1px solid #ccc; padding:6px;">줄 수 (가로×세로)</th>
              <th style="border:1px solid #ccc; padding:6px;">장수</th>
            </tr>
            {detail_rows_html}
          </table>

          <h3 style="color:{AISOL_DARK};">금액 상세</h3>
          <table style="border-collapse:collapse; width:100%; margin-bottom:12px;">
            <tr>
              <td style="border:1px solid #ccc; padding:6px; width:20%;">재료비 합계</td>
              <td style="border:1px solid #ccc; padding:6px;">{total_mat_cost:,} 원</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">시공비 합계</td>
              <td style="border:1px solid #ccc; padding:6px;">{total_install_cost:,} 원</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">합계 (부가세 전)</td>
              <td style="border:1px solid #ccc; padding:6px;">{total_subtotal:,} 원</td>
            </tr>
            <tr>
              <td style="border:1px solid #ccc; padding:6px; font-weight:bold;">최종 견적 (VAT 포함)</td>
              <td style="border:1px solid #ccc; padding:6px; font-weight:bold;">{total_final:,} 원</td>
            </tr>
          </table>
        </div>
        """

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 4. 프린트 버튼 (모든 모드 공통)
# -------------------------
if print_html:
    # 견적서 HTML + JS 프린트 버튼 삽입
    print_button = f"""
    <script>
    function printAisolQuote(){{
        var divContents = document.getElementById('print-area').innerHTML;
        var win = window.open('', '', 'height=900,width=700');
        win.document.write('<html><head><title>아이솔(ISOL) 800 x 800 매트 견적서</title>');
        win.document.write('</head><body>');
        win.document.write(divContents);
        win.document.write('</body></html>');
        win.document.close();
        win.focus();
        win.print();
        win.close();
    }}
    </script>
    {print_html}
    <button onclick="printAisolQuote()" style="
        margin-top:10px;
        padding:8px 16px;
        background-color:{AISOL_MAIN};
        color:white;
        border:none;
        border-radius:6px;
        font-size:14px;
        cursor:pointer;
    ">
      🖨 견적서 프린트하기
    </button>
    """

    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 🖨 견적서 프린트", unsafe_allow_html=True)
    st.markdown(
        "아래 버튼을 누르면 브라우저 인쇄 창이 열리며, 바로 A4 견적서를 출력할 수 있습니다.",
        unsafe_allow_html=True,
    )
    st.markdown(print_button, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
