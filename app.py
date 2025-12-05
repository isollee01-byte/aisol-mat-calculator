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
    .block-co
