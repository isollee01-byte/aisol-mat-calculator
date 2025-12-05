import math
import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# -----------------------------
# 페이지 & 브랜드 설정
# -----------------------------
st.set_page_config(
    page_title="아이솔 800×800 매트 견적 프로그램",
    page_icon="💡",
    layout="centered"
)

PRIMARY = "#7DBFDB"        # 아이솔 시안
PRIMARY_DARK = "#2F3A40"   # 딥 블루/차콜
LIGHT_BG = "#F4F7F9"
ACCENT = "#D9534F"

MATERIAL_PRICES = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}

INSTALL_COST_PER_MAT = 6400  # 장당 시공비

# -----------------------------
# 공통 스타일 (모바일 UX + FAB)
# -----------------------------
st.markdown(
    f"""
    <style>
    body {{ background:{LIGHT_BG}; }}
    .block-container {{
        padding-top:1.4rem;
        padding-bottom:2rem;
        max-width:900px;
    }}
    .aisol-card {{
        background:white;
        padding:18px 22px;
        border-radius:14px;
        margin-bottom:16px;
        border:1px solid #d8dfe6;
        box-shadow:0 2px 4px rgba(0,0,0,0.03);
    }}
    h1, h2, h3, h4 {{
        font-family: "Noto Sans KR", sans-serif;
    }}
    .aisol-button > button {{
        width:100%;
        padding:14px 18px;
        background:{PRIMARY} !important;
        color:white !important;
        border-radius:999px !important;
        font-weight:600;
        border:none;
    }}
    .remove-btn > button {{
        background:#ddd !important;
        color:#333 !important;
        border-radius:10px !important;
        border:none;
        margin-top:20px;
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
    unsafe_allow_html=True
)

# -----------------------------
# 로스 최소화 규칙 (간편모드용)
# -----------------------------
def round_band(x):
    n = math.floor(x)
    frac = x - n
    if frac <= 0.3:
        return n
    elif frac >= 0.6:
        return n + 1
    else:
        return n  # 로스 최소화를 원하므로 중간 구간은 내림

# -----------------------------
# 정밀 계산 함수
# -----------------------------
def calc_mats(width_cm, height_cm):
    w = width_cm / 100
    h = height_cm / 100
    w_count = math.ceil(w / 0.8)
    h_count = math.ceil(h / 0.8)
    return w_count, h_count, w_count * h_count

def quote(mats, material):
    unit_price = MATERIAL_PRICES[material]
    mat_cost = mats * unit_price
    install_cost = mats * INSTALL_COST_PER_MAT
    subtotal = mat_cost + install_cost
    total = math.ceil(subtotal * 1.10)
    return mat_cost, install_cost, subtotal, total

# -----------------------------
# PDF 생성
# -----------------------------
class QuotePDF(FPDF):
    def header(self):
        try:
            self.image("logo_aisol.png", 10, 8, 25)
        except:
            pass
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "아이솔 매트 견적서", ln=1, align="R")

def build_pdf(customer_name, phone, material, rows, totals):
    pdf = QuotePDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"견적일: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    if customer_name:
        pdf.cell(0, 8, f"고객명: {customer_name}", ln=1)
    if phone:
        pdf.cell(0, 8, f"연락처: {phone}", ln=1)
    
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"사용 매트 종류: {material}", ln=1)
    pdf.ln(2)

    headers = ["구역", "가로", "세로", "장수", "재료비", "시공비", "VAT포함"]
    widths = [28, 22, 22, 15, 28, 28, 28]
    pdf.set_font("Helvetica", "", 10)

    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, 1, 0, "C")
    pdf.ln()

    for row in rows:
        pdf.cell(widths[0], 7, row["name"], 1)
        pdf.cell(widths[1], 7, str(row["w"]), 1, 0, "R")
        pdf.cell(widths[2], 7, str(row["h"]), 1, 0, "R")
        pdf.cell(widths[3], 7, str(row["mats"]), 1, 0, "R")
        pdf.cell(widths[4], 7, f'{row["mat_cost"]:,}', 1, 0, "R")
        pdf.cell(widths[5], 7, f'{row["install_cost"]:,}', 1, 0, "R")
        pdf.cell(widths[6], 7, f'{row["total_vat"]:,}', 1, 0, "R")
        pdf.ln()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"최종 합계 (VAT 포함): {totals['final_total']:,} 원", ln=1)

    return pdf.output(dest="S").encode("latin-1")

# -----------------------------
# 헤더
# -----------------------------
st.markdown(
    f"""
    <h1 style="color:{PRIMARY_DARK}; font-weight:700;">
        아이솔 800×800 매트 견적 프로그램
    </h1>
    <p style="color:#6b7683;">
        간편모드 + 정밀모드 · 무제한 구역 추가 · PDF 견적서 생성
    </p>
    """,
    unsafe_allow_html=True,
)

# ================================
#   고객 정보
# ================================
st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    customer_name = st.text_input("고객명")
with c2:
    customer_phone = st.text_input("연락처")
material_type = st.selectbox("매트 종류", MATERIAL_PRICES.keys())
st.markdown('</div>', unsafe_allow_html=True)

# ================================
#   간편모드 계산
# ================================
st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
st.subheader("🧮 간편모드 (평수 기반 계산)")

pyeong = st.number_input("전용면적(평)", min_value=1.0, step=0.1)

if pyeong:
    coef = 0.93
    raw = pyeong * coef

    rounded = round_band(raw)
    final_easy = math.ceil(rounded * 1.10)

    st.write(f"- 평 × 0.93 = {raw:.2f}장")
    st.write(f"- 로스 최소 반올림 적용 → {rounded}장")
    st.write(f"- 최종 +10% 적용 → **{final_easy} 장**")

st.markdown('</div>', unsafe_allow_html=True)

# ================================
#   정밀모드 - 구역 추가 기능
# ================================
st.markdown('<div class="aisol-card">', unsafe_allow_html=True)
st.subheader("📐 정밀모드 (실측 기반 계산)")
st.markdown("필요한 만큼 구역을 자유롭게 추가하세요.")
st.markdown('</div>', unsafe_allow_html=True)

if "zones" not in st.session_state:
    st.session_state.zones = []

remove_idx = None

for i, zone in enumerate(st.session_state.zones):
    st.markdown('<div class="aisol-card">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2,1,1,0.4])
    with col1:
        zone["name"] = st.text_input("구역명", value=zone["name"], key=f"n{i}")
    with col2:
        zone["w"] = st.number_input("가로(cm)", min_value=50, value=zone["w"], key=f"w{i}")
    with col3:
        zone["h"] = st.number_input("세로(cm)", min_value=50, value=zone["h"], key=f"h{i}")
    with col4:
        st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
        if st.button("X", key=f"dx{i}"):
            remove_idx = i
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

if remove_idx is not None:
    st.session_state.zones.pop(remove_idx)

# -----------------------------
# 플로팅 + 버튼
# -----------------------------
st.markdown('<div class="aisol-fab">', unsafe_allow_html=True)
if st.button("+", key="fab_add"):
    st.session_state.zones.append({"name": f"구역 {len(st.session_state.zones)+1}", "w": 120, "h": 120})
st.markdown('</div>', unsafe_allow_html=True)

# ================================
#   계산 버튼
# ================================
st.markdown('<div class="aisol-button">', unsafe_allow_html=True)
run = st.button("정밀 견적 계산하기")
st.markdown('</div>', unsafe_allow_html=True)

# ================================
#   계산 수행
# ================================
if run:

    rows = []
    total_mats = 0

    st.subheader("🧾 구역별 정밀 계산 결과")

    for z in st.session_state.zones:
        wc, hc, mats = calc_mats(z["w"], z["h"])
        mat_cost, inst_cost, subtotal, total = quote(mats, material_type)

        rows.append({
            "name": z["name"],
            "w": z["w"],
            "h": z["h"],
            "mats": mats,
            "mat_cost": mat_cost,
            "install_cost": inst_cost,
            "subtotal": subtotal,
            "total_vat": total
        })

        total_mats += mats

        st.markdown(
            f"""
            <div class="aisol-card">
                <h4 style="color:{PRIMARY_DARK};">{z['name']}</h4>
                <p>가로 줄수: {wc} / 세로 줄수: {hc}</p>
                <p><b>필요 장수: {mats} 장</b></p>
                <p>재료비: {mat_cost:,} 원</p>
                <p>시공비: {inst_cost:,} 원</p>
                <p>합계(부가세 전): {subtotal:,} 원</p>
                <h4 style="color:{ACCENT};">총(VAT 포함): {total:,} 원</h4>
            </div>
            """,
            unsafe_allow_html=True
        )

    mat_total, inst_total, subtotal_total, final_total = quote(total_mats, material_type)

    st.subheader("🎯 전체 총합")

    st.markdown(
        f"""
        <div style="padding:20px;background:{PRIMARY_DARK};border-radius:14px;color:white;">
            <p>총 장수: {total_mats}장</p>
            <p>재료비: {mat_total:,} 원</p>
            <p>시공비: {inst_total:,} 원</p>
            <p>합계(부가세 전): {subtotal_total:,} 원</p>
            <h3 style="color:{PRIMARY};">최종 견적(VAT 포함): {final_total:,} 원</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # PDF 생성
    pdf_bytes = build_pdf(customer_name, customer_phone, material_type, rows, {
        "total_mats": total_mats,
        "final_total": final_total
    })

    st.download_button(
        "📄 견적서 PDF 다운로드",
        data=pdf_bytes,
        file_name="아이솔_견적서.pdf",
        mime="application/pdf"
    )
