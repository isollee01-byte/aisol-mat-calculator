############################################################
#   아이솔(ISOL) 800×800 매트 견적 프로그램 — REFACTORED FINAL
############################################################

import streamlit as st
import streamlit.components.v1 as components
import base64
import pandas as pd
import os
import math
from datetime import datetime

############################################################
#  PAGE CONFIG
############################################################
st.set_page_config(
    page_title="아이솔 800×800 매트 견적 프로그램",
    page_icon="🧩",
    layout="centered"
)

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
def get_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo_center(path: str, width: int = 150):
    b64 = get_base64(path)
    st.markdown(
        f"""
        <div style="text-align:center; margin-bottom:16px;">
            <img src="data:image/png;base64,{b64}" width="{width}">
        </div>
        """,
        unsafe_allow_html=True,
    )

############################################################
#  GLOBAL STYLE (CSS 문자열은 .format 사용, 중괄호 이스케이프)
############################################################
style_html = """
<style>
body {{
  background-color: {bg};
}}
.aisol-card {{
  background:white;
  padding:20px;
  border-radius:14px;
  border:1px solid #d9d9d9;
  margin-bottom:20px;
}}
.stButton > button {{
  background:{main} !important;
  color:white !important;
  border-radius:8px !important;
  height:42px;
  font-size:16px !important;
}}
</style>
""".format(bg=BACKGROUND, main=AISOL_MAIN)

st.markdown(style_html, unsafe_allow_html=True)

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

ZONE_LIST = [
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

LOG_FILE = "quote_log.csv"

############################################################
#  계산 관련 함수
############################################################
def band_round(v: float) -> int:
    base = math.floor(v)
    frac = v - base
    if frac <= 0.3:
        return base
    elif frac >= 0.6:
        return base + 1
    else:
        return base

def calc_precision(w_cm: float, h_cm: float):
    wc = band_round(w_cm / 80.0)
    hc = band_round(h_cm / 80.0)
    wc = max(wc, 1)
    hc = max(hc, 1)
    return wc, hc, wc * hc

def calc_easy(pyeong: float, zone: str, is_extended: bool) -> int:
    mats = pyeong * EASY_FACTORS[zone]
    mats = round(mats)
    if not is_extended:
        mats = max(mats - 8, 0)
    mats = math.ceil(mats * 1.10)  # +10% 여유
    return mats

def calc_quote(mats: int, material: str):
    mat_cost = mats * MATERIAL_PRICE[material]
    inst_cost = mats * INSTALL_PRICE
    subtotal = mat_cost + inst_cost
    total = math.ceil(subtotal * 1.10)  # VAT 10%
    return mat_cost, inst_cost, subtotal, total

############################################################
#  SERIAL NUMBER & CSV 저장
############################################################
def load_last_serial():
    if not os.path.exists(LOG_FILE):
        return None
    df = pd.read_csv(LOG_FILE)
    if len(df) == 0:
        return None
    return df.iloc[-1]["serial"]

def generate_serial() -> str:
    today = datetime.now().strftime("%Y%m%d")
    last = load_last_serial()
    if last and last.startswith(f"ISOL-{today}"):
        num = int(last.split("-")[-1]) + 1
    else:
        num = 1
    return f"ISOL-{today}-{num:03d}"

def save_quote_to_csv(serial, name, phone, address, mode, mats, material, total):
    row = {
        "serial": serial,
        "customer": name,
        "phone": phone,
        "address": address,
        "mode": mode,
        "mats": mats,
        "material": material,
        "total_price": total,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    new_df = pd.DataFrame([row])
    if not os.path.exists(LOG_FILE):
        new_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    else:
        old_df = pd.read_csv(LOG_FILE)
        all_df = pd.concat([old_df, new_df], ignore_index=True)
        all_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

############################################################
#  LOGIN
############################################################
def login_screen():
    show_logo_center("isol_logo.png", width=160)
    st.markdown(
        f"""
        <h2 style="text-align:center; color:{AISOL_DARK};">아이솔(ISOL) 견적 시스템 로그인</h2>
        <p style="text-align:center; color:#777; margin-bottom:20px;">
            승인된 사용자만 접근할 수 있습니다.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="max-width:400px; margin:auto; background:white;
                    border-radius:12px; border:1px solid #ddd; padding:20px;">
        """,
        unsafe_allow_html=True,
    )

    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    login_btn = st.button("로그인", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if login_btn:
        if username == "isol_admin" and password == "isol202512!":
            st.session_state["logged_in"] = True
            st.success("로그인 성공!")
            st.experimental_rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

############################################################
#  메인 헤더
############################################################
show_logo_center("isol_logo.png", width=120)
st.markdown(
    f"<h2 style='text-align:center; color:{AISOL_MAIN};'>아이솔(ISOL) 800×800 매트 견적 프로그램</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='text-align:center; color:{AISOL_DARK};'>간편측정 · 실제측정 기반 프리미엄 매트 견적 산출</p>",
    unsafe_allow_html=True,
)

############################################################
#  고객 정보 입력
############################################################
st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
st.markdown("### 🧾 고객 정보")

c1, c2 = st.columns(2)
with c1:
    customer_name = st.text_input("고객명")
with c2:
    customer_phone = st.text_input("연락처")

address = st.text_input("선택된 주소", key="addr_input")

# 카카오 주소검색 JS (f-string 사용 안 함)
addr_js = """
<script src="https://t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js"></script>
<script>
function openPost(){
    new daum.Postcode({
        oncomplete: function(data){
            var full = data.address;
            var inp = window.parent.document.getElementById("addr_input");
            if(!inp){
                // fallback: 첫 번째 text input 사용
                inp = window.parent.document.querySelector('input[type="text"]');
            }
            if(inp){
                inp.value = full;
                inp.dispatchEvent(new Event('input', { bubbles:true }));
            }
        }
    }).open();
}
</script>
<button onclick="openPost()"
style="margin-top:5px; padding:6px 12px; background:#61A8C9; color:white;
       border:none; border-radius:6px; cursor:pointer;">
📍 주소 검색
</button>
"""
components.html(addr_js, height=70)

desired_date = st.date_input("시공 희망일 선택")

st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  모드 & 재질 선택
############################################################
st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
mode = st.selectbox("계산 모드 선택", ["간편측정", "실제측정"])
material = st.selectbox("매트 재질 선택", list(MATERIAL_PRICE.keys()))
st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  견적 결과 HTML 저장 변수
############################################################
print_html = None

############################################################
#  간편측정 모드
############################################################
if mode == "간편측정":
    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 📏 간편측정 (평수 기반)")

    pyeong = st.number_input("전용 면적 (평)", min_value=1.0, step=0.5)
    zone_type = st.selectbox("시공 범위", list(EASY_FACTORS.keys()))
    ext = st.radio("확장형 여부", ["확장형", "비확장형"], horizontal=True)

    if st.button("간편측정 계산하기"):
        mats = calc_easy(pyeong, zone_type, ext == "확장형")
        mat_cost, inst_cost, subtotal, total = calc_quote(mats, material)

        st.success(f"총 필요 매트: {mats} 장")
        st.info(f"최종 견적(VAT 포함): {total:,} 원")

        serial = generate_serial()
        save_quote_to_csv(serial, customer_name, customer_phone, address, mode, mats, material, total)

        logo_b64 = get_base64("isol_logo.png")
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        print_html = f"""
        <div id="print-area" style="position:relative; padding:20px; font-family:Arial, sans-serif;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="position:absolute; top:25%; left:20%; width:350px; opacity:0.08; z-index:-1;">
            <h2 style="color:{AISOL_MAIN}; margin-bottom:4px;">아이솔(ISOL) 매트 견적서</h2>
            <p style="margin-top:0;">일련번호: <b>{serial}</b></p>
            <p>견적일자: {today}</p>

            <h3 style="color:{AISOL_DARK};">고객 정보</h3>
            <p>고객명: {customer_name}</p>
            <p>연락처: {customer_phone}</p>
            <p>주소: {address}</p>
            <p>시공 희망일: {desired_date}</p>

            <h3 style="color:{AISOL_DARK};">견적 요약</h3>
            <p>계산 방식: 간편측정</p>
            <p>시공 범위: {zone_type}</p>
            <p>매트 재질: {material}</p>
            <p>총 필요 매트: {mats} 장</p>

            <h3 style="color:{AISOL_DARK};">금액 상세</h3>
            <p>재료비: {mat_cost:,} 원</p>
            <p>시공비: {inst_cost:,} 원</p>
            <p><b>최종 견적 (VAT 포함): {total:,} 원</b></p>
        </div>
        """

    st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  실제측정 모드
############################################################
if mode == "실제측정":
    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 📐 실제측정 (실측 기반)")

    zone_count = st.number_input("측정할 구역 수", min_value=1, max_value=20, value=1)

    zones = []
    for i in range(int(zone_count)):
        c1, c2, c3 = st.columns(3)
        with c1:
            ztype = st.selectbox(f"구역 {i+1}", ZONE_LIST, key=f"ztype_{i}")
        with c2:
            w = st.number_input(f"가로 {i+1} (cm)", min_value=40.0, key=f"w_{i}")
        with c3:
            h = st.number_input(f"세로 {i+1} (cm)", min_value=40.0, key=f"h_{i}")
        zones.append({"type": ztype, "w": w, "h": h})

    if st.button("실제측정 계산하기"):
        total_mats = 0
        rows_html = ""

        for z in zones:
            wc, hc, mats = calc_precision(z["w"], z["h"])
            total_mats += mats
            rows_html += f"""
            <tr>
              <td style="border:1px solid #ccc; padding:6px;">{z['type']}</td>
              <td style="border:1px solid #ccc; padding:6px;">{z['w']} × {z['h']} cm</td>
              <td style="border:1px solid #ccc; padding:6px;">{wc} × {hc}</td>
              <td style="border:1px solid #ccc; padding:6px; text-align:right;">{mats}</td>
            </tr>
            """

        mat_cost, inst_cost, subtotal, total = calc_quote(total_mats, material)

        st.success(f"총 필요 매트: {total_mats} 장")
        st.info(f"최종 견적(VAT 포함): {total:,} 원")

        serial = generate_serial()
        save_quote_to_csv(serial, customer_name, customer_phone, address, mode, total_mats, material, total)

        logo_b64 = get_base64("isol_logo.png")
        today = datetime.now().strftime("%Y-%m-%d %H:%M")

        print_html = f"""
        <div id="print-area" style="position:relative; padding:20px; font-family:Arial, sans-serif;">
            <img src="data:image/png;base64,{logo_b64}"
                 style="position:absolute; top:25%; left:20%; width:350px; opacity:0.08; z-index:-1;">

            <h2 style="color:{AISOL_MAIN}; margin-bottom:4px;">아이솔(ISOL) 매트 견적서</h2>
            <p style="margin-top:0;">일련번호: <b>{serial}</b></p>
            <p>견적일자: {today}</p>

            <h3 style="color:{AISOL_DARK};">고객 정보</h3>
            <p>고객명: {customer_name}</p>
            <p>연락처: {customer_phone}</p>
            <p>주소: {address}</p>
            <p>시공 희망일: {desired_date}</p>

            <h3 style="color:{AISOL_DARK};">구역별 실측 정보</h3>
            <table style="border-collapse:collapse; width:100%; border:1px solid #ccc;">
                <tr style="background:{AISOL_LIGHT};">
                    <th style="border:1px solid #ccc; padding:6px;">구역</th>
                    <th style="border:1px solid #ccc; padding:6px;">실측(cm)</th>
                    <th style="border:1px solid #ccc; padding:6px;">줄 수</th>
                    <th style="border:1px solid #ccc; padding:6px;">장수</th>
                </tr>
                {rows_html}
            </table>

            <h3 style="color:{AISOL_DARK};">금액 요약</h3>
            <p>재료비: {mat_cost:,} 원</p>
            <p>시공비: {inst_cost:,} 원</p>
            <p><b>최종 견적 (VAT 포함): {total:,} 원</b></p>
        </div>
        """

    st.markdown("</div>", unsafe_allow_html=True)

############################################################
#  프린트 섹션
############################################################
if print_html:
    html_page = """
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
      {content}
      <button onclick="window.print()"
        style="margin-top:20px; padding:10px 20px; background:{main}; color:white;
               border:none; border-radius:6px; cursor:pointer;">
        🖨 견적서 인쇄하기
      </button>
    </body>
    </html>
    """.format(content=print_html, main=AISOL_MAIN)

    st.markdown("<div class='aisol-card'>", unsafe_allow_html=True)
    st.markdown("### 🖨 견적서 프린트")
    components.html(html_page, height=900, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)
