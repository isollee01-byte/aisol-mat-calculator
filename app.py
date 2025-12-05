############################################################
#   아이솔(ISOL) 800×800 매트 견적 프로그램 — FINAL VERSION
#   포함 기능:
#   - 로그인(로고 포함)
#   - 주소 검색(카카오 API)
#   - 달력 선택
#   - 간편측정 모드
#   - 실제측정 모드
#   - 0.3/0.6 줄수 반올림 규칙(정밀모드)
#   - 견적서 프린트(HTML)
#   - 로고 워터마크
#   - 자동 일련번호 생성
#   - 견적 DB 저장(CSV)
############################################################

import streamlit as st
import streamlit.components.v1 as components
import base64
import pandas as pd
import os
import math
from datetime import datetime

############################################################
#  BRAND SETTINGS
############################################################
AISOL_MAIN = "#61A8C9"
AISOL_DARK = "#3A667A"
AISOL_LIGHT = "#E8F4FA"
BACKGROUND = "#F5F7FB"

############################################################
#  LOGO BASE64
############################################################
def get_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo_center(path, width=150):
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:20px;">
            <img src="data:image/png;base64,{get_base64(path)}" width="{width}">
        </div>
        """,
        unsafe_allow_html=True,
    )

############################################################
#  LOGIN SCREEN
############################################################
def login_screen():
    show_logo_center("isol_logo.png", width=160)

    st.markdown(
        f"""
        <h2 style="text-align:center; color:{AISOL_DARK};">아이솔(ISOL) 견적 로그인</h2>
        <p style="text-align:center; color:#777;">승인된 사용자만 접근 가능합니다.</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="max-width:400px; margin:auto; padding:20px; background:white;
                    border-radius:12px; border:1px solid #ccc;">
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    login_btn = st.button("로그인", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if login_btn:
        if username == "isol_admin" and password == "isol202512!":
            st.session_state.logged_in = True
            st.success("로그인 성공!")
            st.experimental_rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
    st.stop()

############################################################
#  PAGE CONFIG + UI STYLE
############################################################
st.set_page_config(page_title="아이솔 800×800 매트 견적 프로그램", page_icon="🧩")

st.markdown(
    f"""
    <style>
        body {{ background:{BACKGROUND}; }}
        .aisol-card {{
            background:white;
            padding:20px;
            border-radius:14px;
            border:1px solid #d9d9d9;
            margin-bottom:20px;
        }}
        .stButton>button {{
            background:{AISOL_MAIN} !important;
            color:white !important;
            border-radius:8px !important;
            height:42px;
            font-size:16px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

############################################################
#  CONSTANTS
############################################################
MATERIAL_PRICE = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}
INSTALL_PRICE = 6400

EASY_FACTORS = {
    "거실": 0.93,
    "거실 + 복도": 1.46,
    "거실 + 복도 + 아이방1": 1.67,
    "거실 + 복도 + 주방": 2.0,
}

ZONE_LIST = ["거실","복도","아일랜드","주방","안방","아이방1","아이방2","아이방3","알파룸"]

############################################################
#  NUMBER ROUNDING LOGIC (정밀모드)
############################################################
def band_round(v):
    base = math.floor(v)
    frac = v - base
    if frac <= 0.3:
        return base
    elif frac >= 0.6:
        return base + 1
    else:
        return base

def calc_precision(w, h):
    wc = band_round(w / 80)
    hc = band_round(h / 80)
    wc = max(wc, 1)
    hc = max(hc, 1)
    return wc, hc, wc * hc

############################################################
#  EASY MODE
############################################################
def calc_easy(p, zone, ext):
    mats = p * EASY_FACTORS[zone]
    mats = round(mats)
    if not ext:
        mats = max(mats - 8, 0)
    mats = math.ceil(mats * 1.10)
    return mats

############################################################
#  QUOTE CALCULATION
############################################################
def calc_quote(mats, material):
    mat_cost = mats * MATERIAL_PRICE[material]
    inst_cost = mats * INSTALL_PRICE
    subtotal = mat_cost + inst_cost
    total = math.ceil(subtotal * 1.10)
    return mat_cost, inst_cost, subtotal, total

############################################################
#  SERIAL NUMBER SYSTEM
############################################################
LOG_FILE = "quote_log.csv"

def load_last_serial():
    if not os.path.exists(LOG_FILE):
        return None
    df = pd.read_csv(LOG_FILE)
    if len(df) == 0:
        return None
    return df.iloc[-1]["serial"]

def generate_serial():
    today = datetime.now().strftime("%Y%m%d")
    last = load_last_serial()

    if last and last.startswith(f"ISOL-{today}"):
        num = int(last.split("-")[-1]) + 1
    else:
        num = 1

    return f"ISOL-{today}-{num:03d}"

def save_quote(serial, name, phone, addr, mode, mats, material, total):
    row = {
        "serial": serial,
        "customer": name,
        "phone": phone,
        "address": addr,
        "mode": mode,
        "mats": mats,
        "material": material,
        "total": total,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    df = pd.DataFrame([row])
    if not os.path.exists(LOG_FILE):
        df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    else:
        old = pd.read_csv(LOG_FILE)
        new = pd.concat([old, df], ignore_index=True)
        new.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

############################################################
#  MAIN HEADER
############################################################
show_logo_center("isol_logo.png", width=120)
st.markdown(f"<h2 style='text-align:center; color:{AISOL_MAIN};'>아이솔 800×800 매트 견적 프로그램</h2>", unsafe_allow_html=True)

############################################################
#  CUSTOMER INFORMATION
############################################################
st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
st.markdown("### 🧾 고객 정보")

col1, col2 = st.columns(2)
with col1:
    cname = st.text_input("고객명")
with col2:
    cphone = st.text_input("연락처")

addr = st.text_input("선택된 주소", key="addr_input")

# 주소 검색 버튼
addr_js = f"""
<script src="https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js"></script>
<script>
function openPost(){
    new daum.Postcode({{
        oncomplete: function(data){{
            let full = data.address;
            let inp = window.parent.document.getElementById("addr_input");
            inp.value = full;
            inp.dispatchEvent(new Event('input', {{ bubbles:true }}));
        }}
    }}).open();
}
</script>
<button onclick="openPost()" 
style="margin-top:5px; padding:6px 12px; background:{AISOL_MAIN}; color:white; border:none; border-radius:6px;">
📍 주소 검색
</button>
"""
components.html(addr_js, height=60)

cdate = st.date_input("시공 희망일 선택")

st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  MODE & MATERIAL
############################################################
st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)

mode = st.selectbox("계산 모드 선택", ["간편측정", "실제측정"])
material = st.selectbox("매트 재질 선택", list(MATERIAL_PRICE.keys()))

st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  CALCULATE
############################################################
print_html = None

############################################################
#  EASY MODE
############################################################
if mode == "간편측정":
    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)

    p = st.number_input("전용 면적(평)", min_value=1.0)
    zone = st.selectbox("시공 범위", list(EASY_FACTORS.keys()))
    ext = st.radio("확장형 여부", ["확장형", "비확장형"])

    if st.button("간편측정 계산"):
        mats = calc_easy(p, zone, ext=="확장형")
        mat_cost, inst_cost, subtotal, total = calc_quote(mats, material)

        st.success(f"총 필요 매트: {mats} 장")
        st.info(f"최종 금액(VAT 포함): {total:,} 원")

        serial = generate_serial()
        save_quote(serial, cname, cphone, addr, mode, mats, material, total)

        logo_b64 = get_base64("isol_logo.png")
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        print_html = f"""
        <div id='print-area' style="position:relative; padding:20px;">
            <img src="data:image/png;base64,{logo_b64}" 
                 style="position:absolute; top:25%; left:20%; width:350px; opacity:0.08; z-index:-1;">
            <h2 style="color:{AISOL_MAIN};">아이솔(ISOL) 매트 견적서</h2>
            <p>일련번호: <b>{serial}</b></p>
            <p>견적일자: {today}</p>
            <h3>고객 정보</h3>
            <p>이름: {cname}</p>
            <p>연락처: {cphone}</p>
            <p>주소: {addr}</p>
            <p>희망일: {cdate}</p>
            <h3>견적 요약</h3>
            <p>방식: 간편측정</p>
            <p>필요 매트: {mats} 장</p>
            <p>재질: {material}</p>
            <h3>금액 상세</h3>
            <p>재료비: {mat_cost:,} 원</p>
            <p>시공비: {inst_cost:,} 원</p>
            <p><b>최종금액(VAT포함): {total:,} 원</b></p>
        </div>
        """

    st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  PRECISION MODE
############################################################
if mode == "실제측정":
    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)

    cnt = st.number_input("구역 수", min_value=1, max_value=20, value=1)

    zones = []
    for i in range(cnt):
        col1, col2, col3 = st.columns(3)
        ztype = col1.selectbox(f"구역 {i+1}", ZONE_LIST, key=f"zt{i}")
        w = col2.number_input(f"가로{i+1}(cm)", min_value=40.0, key=f"w{i}")
        h = col3.number_input(f"세로{i+1}(cm)", min_value=40.0, key=f"h{i}")
        zones.append({"type":ztype, "w":w, "h":h})

    if st.button("실제로 계산하기"):

        rows = ""
        total_mats = 0

        for z in zones:
            wc, hc, mats = calc_precision(z["w"], z["h"])
            total_mats += mats

            rows += f"""
            <tr>
               <td>{z['type']}</td>
               <td>{z['w']} × {z['h']} cm</td>
               <td>{wc} × {hc}</td>
               <td style="text-align:right">{mats}</td>
            </tr>
            """

        mat_cost, inst_cost, subtotal, total = calc_quote(total_mats, material)

        st.success(f"총 매트: {total_mats} 장")
        st.info(f"최종 금액(VAT 포함): {total:,} 원")

        serial = generate_serial()
        save_quote(serial, cname, cphone, addr, mode, total_mats, material, total)

        logo_b64 = get_base64("isol_logo.png")
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        print_html = f"""
        <div id='print-area' style="position:relative; padding:20px;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="position:absolute; top:25%; left:20%; width:350px; opacity:0.07; z-index:-1;">
            <h2 style="color:{AISOL_MAIN};">아이솔(ISOL) 매트 견적서</h2>
            <p>일련번호: <b>{serial}</b></p>
            <p>날짜: {today}</p>

            <h3>고객 정보</h3>
            <p>이름: {cname}</p>
            <p>연락처: {cphone}</p>
            <p>주소: {addr}</p>
            <p>희망일: {cdate}</p>

            <h3>실측 정보</h3>
            <table border="1" style="border-collapse: collapse; width:100%;">
                <tr style="background:{AISOL_LIGHT};">
                    <th>구역</th><th>실측(cm)</th><th>줄 수</th><th>장수</th>
                </tr>
                {rows}
            </table>

            <h3>금액 요약</h3>
            <p>재료비: {mat_cost:,} 원</p>
            <p>시공비: {inst_cost:,} 원</p>
            <p><b>최종금액(VAT 포함): {total:,} 원</b></p>
        </div>
        """

    st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  PRINT OUTPUT
############################################################
if print_html:
    html_page = f"""
    <html>
    <head>
        <style>
            @media print {{
                button {{ display:none; }}
                body {{ margin:0; padding:0; }}
            }}
        </style>
    </head>
    <body>
        {print_html}
        <button onclick="window.print()" 
            style="padding:10px 20px; background:{AISOL_MAIN}; color:white;
                   border:none; border-radius:6px; margin-top:20px;">
            🖨 인쇄하기
        </button>
    </body>
    </html>
    """

    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 🖨 견적서 프린트")
    components.html(html_page, height=900, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)
