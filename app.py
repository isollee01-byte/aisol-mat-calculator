import math
from datetime import datetime

import streamlit as st
from fpdf import FPDF

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="아이솔 800×800 매트 견적 프로그램",
    page_icon="💡",
    layout="centered",
)

PRIMARY = "#7DBFDB"
PRIMARY_DARK = "#2F3A40"
LIGHT_BG = "#F4F7F9"
ACCENT = "#D9534F"

MATERIAL_PRICES = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}
INSTALL_COST_PER_MAT = 6400  # 장당 시공비

# ===============================
# 스타일
# ===============================
st.markdown(
    f"""
    <style>
    body {{ background:{LIGHT_BG}; }}
    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }}
    .aisol-card {{
        background: white;
        padding: 16px 20px;
        border-radius: 14px;
        margin-bottom: 16px;
        border: 1px solid #d8dfe6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }}
    .aisol-button > button {{
        width: 100%;
        padding: 12px 16px;
        background: {PRIMARY} !important;
        color: white !important;
        border-radius: 999px !important;
        font-weight: 600;
        border: none;
    }}
    .remove-btn > button {{
        background:#ddd !important;
        color:#333 !important;
        border-radius:10px !important;
        border:none;
        margin-top:22px;
    }}
    .aisol-fab {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }}
    .aisol-fab > button {{
        background:{PRIMARY_DARK} !important;
        color:white !important;
        border-radius:50% !important;
        width:56px;
        height:56px;
        font-size:26px;
        border:none;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===============================
# 공통 함수
# ===============================

def band_round(x: float) -> int:
    """0.3 이하 버림, 0.6 이상 올림, 그 사이 내림."""
    n = math.floor(x)
    frac = x - n
    if frac <= 0.3:
        return n
    elif frac >= 0.6:
        return n + 1
    else:
        return n


def calc_easy_mode(pyeong: float, area_type: str, is_extended: bool):
    """간편모드: 평수 × 계수 → 장수, 확장/비확장, 반올림 규칙."""
    coef_map = {
        "거실": 0.93,
        "거실 + 복도": 1.46,
        "거실 + 복도 + 아이방1": 1.67,
        "거실 + 복도 + 주방": 2.00,
    }
    coef = coef_map[area_type]

    raw = pyeong * coef  # 순수 계산 장수 (float)
    rounded = band_round(raw)

    # 비확장형이면 -8장 (최소 0)
    if not is_extended:
        rounded = max(rounded - 8, 0)

    return raw, rounded  # raw float, rounded int (아직 +10% 적용 전)


def calc_mats_precision(width_cm: float, height_cm: float):
    """정밀모드: 가로/세로(cm) → 줄 수 및 장수 (항상 ceil)."""
    w_m = width_cm / 100
    h_m = height_cm / 100
    w_count = math.ceil(w_m / 0.8)
    h_count = math.ceil(h_m / 0.8)
    total = w_count * h_count
    return w_count, h_count, total


def quote(mats: int, material: str):
    """장수와 자재 종류로 재료비/시공비/부가세 포함 총견적 계산."""
    unit_price = MATERIAL_PRICES[material]
    material_cost = mats * unit_price
    install_cost = mats * INSTALL_COST_PER_MAT
    subtotal = material_cost + install_cost
    total = math.ceil(subtotal * 1.10)  # VAT 10%
    return material_cost, install_cost, subtotal, total


# ===============================
# PDF (영문 전용 – 한글은 안 넣음)
# ===============================

class QuotePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "AISOL Mat Quotation", ln=1, align="R")


def build_pdf(material_type: str, rows: list, totals: dict) -> bytes:
    """
    rows: [{label, mats, mat_cost, install_cost, total_vat}, ...]
    totals: {"total_mats", "final_total"}
    """
    pdf = QuotePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)

    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.cell(0, 8, f"Material: {material_type}", ln=1)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Zones", ln=1)
    pdf.set_font("Helvetica", "", 10)

    headers = ["Zone", "Mats", "MatCost", "Install", "Total(VAT)"]
    widths = [40, 20, 35, 35, 40]

    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, 1, 0, "C")
    pdf.ln()

    for row in rows:
        pdf.cell(widths[0], 7, row["label"], 1)
        pdf.cell(widths[1], 7, str(row["mats"]), 1, 0, "R")
        pdf.cell(widths[2], 7, f'{row["mat_cost"]:,}', 1, 0, "R")
        pdf.cell(widths[3], 7, f'{row["install_cost"]:,}', 1, 0, "R")
        pdf.cell(widths[4], 7, f'{row["total_vat"]:,}', 1, 0, "R")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Total mats: {totals['total_mats']}", ln=1)
    pdf.cell(0, 8, f"Grand Total (VAT): {totals['final_total']:,}", ln=1)

    return pdf.output(dest="S").encode("latin-1")


# ===============================
# 상태 초기화
# ===============================
if "zones" not in st.session_state:
    st.session_state.zones = []  # 정밀모드 구역 리스트


# ===============================
# 헤더
# ===============================
st.markdown(
    f"""
    <h1 style="color:{PRIMARY_DARK}; font-weight:700;">
        아이솔 800×800 매트 견적 프로그램
    </h1>
    <p style="color:#6b7683; margin-top:-6px;">
        간편모드(평수) + 정밀모드(실측) · 정밀모드가 있으면 정밀 기준으로 최종 견적을 산출합니다.
    </p>
    """,
    unsafe_allow_html=True,
)

# ===============================
# 상단 공통: 자재 선택
# ===============================
st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
material_type = st.selectbox("사용할 매트 종류", list(MATERIAL_PRICES.keys()))
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 간편모드
# ===============================
st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
st.subheader("🧮 간편모드 (평수 기반 계산)")

pyeong = st.number_input("전용면적(평)", min_value=0.0, step=0.1)

area_type = st.selectbox(
    "시공 범위 선택",
    ["거실", "거실 + 복도", "거실 + 복도 + 아이방1", "거실 + 복도 + 주방"],
)

is_extended = (
    st.radio("확장형 여부", ["확장형", "비확장형"], horizontal=True) == "확장형"
)

easy_raw = None
easy_rounded = None
easy_final_mats = None
easy_final_total = None

if pyeong > 0:
    easy_raw, easy_rounded = calc_easy_mode(pyeong, area_type, is_extended)
    # 최종 장수(+10% 여유)는 정밀모드가 없을 때만 최종 견적에 사용
    easy_final_mats = math.ceil(easy_rounded * 1.10)

    st.write(f"- 기본 계산: {pyeong:.1f}평 × 계수 → {easy_raw:.2f} 장")
    st.write(f"- 반올림 규칙 후 장수: {easy_rounded} 장")
    if not is_extended:
        st.write(f"  (비확장형: -8장 적용 포함)")
    st.write(f"- 최종(+10% 여유) 장수: **{easy_final_mats} 장**")

st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 정밀모드 - 구역 입력
# ===============================
st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
st.subheader("📐 정밀모드 (실측 기반 구역별 계산)")
st.markdown("실측한 구역을 원하는 만큼 추가하고, 가로·세로(cm)를 입력하세요.")
st.markdown('</div>', unsafe_allow_html=True)

remove_index = None
for i, zone in enumerate(st.session_state.zones):
    st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2, 1, 1, 0.5])
    with c1:
        zone["name"] = st.text_input("구역명", value=zone["name"], key=f"name{i}")
    with c2:
        zone["w"] = st.number_input(
            "가로(cm)", min_value=50, value=int(zone["w"]), key=f"w{i}"
        )
    with c3:
        zone["h"] = st.number_input(
            "세로(cm)", min_value=50, value=int(zone["h"]), key=f"h{i}"
        )
    with c4:
        st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
        if st.button("삭제", key=f"del{i}"):
            remove_index = i
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if remove_index is not None:
    st.session_state.zones.pop(remove_index)

# 플로팅 + 버튼 (구역 추가)
st.markdown('<div class="aisol-fab">', unsafe_allow_html=True)
if st.button("+", key="fab-add"):
    st.session_state.zones.append(
        {"name": f"구역 {len(st.session_state.zones)+1}", "w": 120, "h": 120}
    )
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 계산 버튼
# ===============================
st.markdown('<div class="aisol-button">', unsafe_allow_html=True)
run = st.button("견적 계산하기")
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 계산 / 최종 견적
# ===============================
if run:
    final_source = None          # "easy" or "precision"
    final_mats = None
    final_total = None
    pdf_rows = []

    # 1) 정밀모드 구역이 있는 경우 → 정밀모드 우선
    if len(st.session_state.zones) > 0:
        st.subheader("🧾 정밀모드 구역별 계산 결과")

        total_mats_precision = 0
        material_total_precision = 0
        install_total_precision = 0

        for idx, zone in enumerate(st.session_state.zones, start=1):
            wc, hc, mats = calc_mats_precision(zone["w"], zone["h"])
            mat_cost, inst_cost, subtotal, total = quote(mats, material_type)

            total_mats_precision += mats
            material_total_precision += mat_cost
            install_total_precision += inst_cost

            st.markdown(
                f"""
                <div class="aisol-card">
                    <h4 style="color:{PRIMARY_DARK}; margin-bottom:6px;">{zone['name']}</h4>
                    <p>가로 줄수: {wc} 줄 / 세로 줄수: {hc} 줄</p>
                    <p><b>필요 장수:</b> {mats} 장</p>
                    <p>재료비: {mat_cost:,} 원</p>
                    <p>시공비: {inst_cost:,} 원</p>
                    <p>합계(부가세 전): {subtotal:,} 원</p>
                    <h4 style="color:{ACCENT};">총 견적(VAT 포함): {total:,} 원</h4>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # PDF용 행 (영문 label로만)
            pdf_rows.append(
                {
                    "label": f"Zone {idx}",
                    "mats": mats,
                    "mat_cost": mat_cost,
                    "install_cost": inst_cost,
                    "total_vat": total,
                }
            )

        _, _, subtotal_total_precision, final_total_precision = quote(
            total_mats_precision, material_type
        )

        final_source = "precision"
        final_mats = total_mats_precision
        final_total = final_total_precision

        st.subheader("🎯 최종 견적 (정밀모드 기준)")
        st.markdown(
            f"""
            <div style="padding:20px;background:{PRIMARY_DARK};border-radius:14px;color:white;">
                <p>총 장수: {final_mats} 장</p>
                <p>재료비 총합: {material_total_precision:,} 원</p>
                <p>시공비 총합: {install_total_precision:,} 원</p>
                <p>합계(부가세 전): {subtotal_total_precision:,} 원</p>
                <h3 style="color:{PRIMARY};">최종 견적(VAT 포함): {final_total:,} 원</h3>
                <p style="font-size:0.8rem;opacity:0.7;">
                    ※ 정밀모드 실측 값이 존재하므로 간편모드 결과보다 우선합니다.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        totals_for_pdf = {
            "total_mats": final_mats,
            "final_total": final_total,
        }

    # 2) 정밀모드가 없고, 간편모드 값이 있는 경우 → 간편모드 사용
    elif easy_final_mats is not None:
        final_source = "easy"
        final_mats = easy_final_mats
        mat_cost, inst_cost, subtotal, final_total = quote(final_mats, material_type)

        st.subheader("🎯 최종 견적 (간편모드 기준)")
        st.markdown(
            f"""
            <div style="padding:20px;background:{PRIMARY_DARK};border-radius:14px;color:white;">
                <p>총 장수: {final_mats} 장</p>
                <p>재료비: {mat_cost:,} 원</p>
                <p>시공비: {inst_cost:,} 원</p>
                <p>합계(부가세 전): {subtotal:,} 원</p>
                <h3 style="color:{PRIMARY};">최종 견적(VAT 포함): {final_total:,} 원</h3>
                <p style="font-size:0.8rem;opacity:0.7;">
                    ※ 정밀모드 구역이 없으므로 평수 기반 간편 계산 결과를 사용합니다.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pdf_rows.append(
            {
                "label": "EasyMode",
                "mats": final_mats,
                "mat_cost": mat_cost,
                "install_cost": inst_cost,
                "total_vat": final_total,
            }
        )
        totals_for_pdf = {
            "total_mats": final_mats,
            "final_total": final_total,
        }

    else:
        st.warning("간편모드 평수 또는 정밀모드 구역 중 하나 이상은 입력해야 합니다.")
        final_source = None
        totals_for_pdf = None

    # ===============================
    # PDF 다운로드 (ASCII만 사용)
    # ===============================
    if final_source and totals_for_pdf is not None:
        pdf_bytes = build_pdf(material_type, pdf_rows, totals_for_pdf)
        st.download_button(
            "📄 견적서 PDF 다운로드",
            data=pdf_bytes,
            file_name="aisol_quote.pdf",
            mime="application/pdf",
        )
