import streamlit as st
import math
from fpdf import FPDF
from datetime import datetime

# =========================
#  AISOL BRAND COLOR
# =========================
AISOL_MAIN = "#61A8C9"   # 대표 컬러
AISOL_DARK = "#3A667A"
AISOL_LIGHT = "#A7D1E6"

st.set_page_config(
    page_title="아이솔 800x800 매트 견적 프로그램",
    page_icon="🧩",
    layout="centered"
)

st.markdown(
    f"""
    <style>
        .main-title {{
            color: {AISOL_MAIN};
            text-align: center;
            font-size: 32px;
            font-weight: 700;
        }}
        .subtitle {{
            color: {AISOL_DARK};
            font-size: 20px;
            font-weight: 600;
            margin-top: -10px;
            text-align: center;
        }}
        .stButton>button {{
            background-color: {AISOL_MAIN};
            color: white;
            border-radius: 8px;
            height: 45px;
            font-size: 18px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='main-title'>AISOL 800×800 매트 견적 프로그램</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>간편모드 · 정밀모드 기반 최적 매트 산출</div>", unsafe_allow_html=True)

# =========================
# 반올림 규칙 (옵션 C 적용)
# =========================
def band_round_ratio(value):
    """ 옵션 C : 가로/세로 줄 수에 직접 반올림 적용 """
    base = math.floor(value)
    frac = value - base
    if frac <= 0.3:
        return base
    elif frac >= 0.6:
        return base + 1
    else:
        return base

# =========================
# 정밀 모드 매트 계산
# =========================
def calc_precision(w_cm, h_cm):
    w_ratio = w_cm / 80
    h_ratio = h_cm / 80

    w_count = band_round_ratio(w_ratio)
    h_count = band_round_ratio(h_ratio)

    if w_count < 1: w_count = 1
    if h_count < 1: h_count = 1

    return w_count, h_count, w_count * h_count

# =========================
# 간편모드 평균값
# =========================
EASY_FACTORS = {
    "거실": 0.93,
    "거실 + 복도": 1.46,
    "거실 + 복도 + 아이방1": 1.67,
    "거실 + 복도 + 주방": 2.0
}

# =========================
# 가격 테이블
# =========================
MATERIAL_PRICE = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000
}

INSTALL_PRICE = 6400

# =========================
# PDF 클래식 (영문 전용)
# =========================
class QuotePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "AISOL Mat Quotation", ln=1, align="R")

def build_pdf(material, rows, totals):
    mp = {
        "일반 TPU": "Standard TPU",
        "프리미엄 TPU": "Premium TPU",
        "패브릭 TPU": "Fabric TPU"
    }
    mat_label = mp.get(material, "TPU")

    pdf = QuotePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)

    pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.cell(0, 8, f"Material: {mat_label}", ln=1)
    pdf.ln(5)

    headers = ["Zone", "WxH", "Mats", "MatCost", "Install", "Total(VAT)"]
    widths = [30, 40, 20, 30, 30, 40]

    pdf.set_font("Helvetica", "B", 10)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, 1, 0, "C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 10)

    for r in rows:
        pdf.cell(widths[0], 7, r["label"], 1)
        pdf.cell(widths[1], 7, r["wh"], 1)
        pdf.cell(widths[2], 7, str(r["mats"]), 1, 0, "R")
        pdf.cell(widths[3], 7, f"{r['mat_cost']:,}", 1, 0, "R")
        pdf.cell(widths[4], 7, f"{r['install_cost']:,}", 1, 0, "R")
        pdf.cell(widths[5], 7, f"{r['total_vat']:,}", 1, 0, "R")
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, f"Total Mats: {totals['mats']}", ln=1)
    pdf.cell(0, 7, f"Final Total (VAT): {totals['final']:,}", ln=1)

    return pdf.output(dest="S").encode("latin-1")

# =========================
# 입력 UI
# =========================
mode = st.selectbox("계산 모드를 선택하세요", ["간편모드", "정밀모드"])
material = st.selectbox("재질 선택", list(MATERIAL_PRICE.keys()))

rows_pdf = []
total_mats = 0
total_final_cost = 0

# -------------------------
# ⭐ 간편모드
# -------------------------
if mode == "간편모드":
    pyeong = st.number_input("평수 입력", 1, 100)
    area_opt = st.selectbox("시공 구역 선택", list(EASY_FACTORS.keys()))
    expand = st.selectbox("확장 여부", ["확장형", "비확장형"])

    if st.button("계산하기"):
        mats = pyeong * EASY_FACTORS[area_opt]

        if expand == "비확장형":
            mats -= 8

        mats = max(1, round(mats))

        mats_final = int(mats * 1.10)  # +10%

        total_mats = mats_final
        mat_cost = total_mats * MATERIAL_PRICE[material]
        install_cost = total_mats * INSTALL_PRICE
        vat = int((mat_cost + install_cost) * 1.1)

        total_final_cost = vat

        rows_pdf.append({
            "label": "EasyMode",
            "wh": f"{pyeong}평",
            "mats": total_mats,
            "mat_cost": mat_cost,
            "install_cost": install_cost,
            "total_vat": vat
        })

        st.success(f"총 필요 매트 수: {total_mats}장")
        st.info(f"최종 견적(VAT 포함): {vat:,} 원")

# -------------------------
# ⭐ 정밀모드 (옵션 C 적용)
# -------------------------
if mode == "정밀모드":
    st.subheader("실측 입력 (단위: cm)")

    num = st.number_input("구역 개수", 1, 10)

    zones = []
    for i in range(num):
        w = st.number_input(f"{i+1}번 구역 가로(cm)", 50)
        h = st.number_input(f"{i+1}번 구역 세로(cm)", 50)
        zones.append((w, h))

    if st.button("계산하기"):
        for idx, (w, h) in enumerate(zones):
            wc, hc, mats = calc_precision(w, h)
            mats = max(1, mats)

            mat_cost = mats * MATERIAL_PRICE[material]
            install_cost = mats * INSTALL_PRICE
            total = int((mat_cost + install_cost) * 1.1)

            total_mats += mats
            total_final_cost += total

            rows_pdf.append({
                "label": f"Z{idx+1}",
                "wh": f"{w}x{h}",
                "mats": mats,
                "mat_cost": mat_cost,
                "install_cost": install_cost,
                "total_vat": total
            })

        st.success(f"총 필요 매트 수: {total_mats}장")
        st.info(f"최종 견적(VAT 포함): {total_final_cost:,} 원")

# -------------------------
# PDF 다운로드
# -------------------------
if total_mats > 0:
    pdf_bytes = build_pdf(material, rows_pdf, {"mats": total_mats, "final": total_final_cost})
    st.download_button("PDF 견적서 다운로드", pdf_bytes, "aisol_quotation.pdf")
