import base64
from datetime import datetime, date
from io import BytesIO
import math
import os

import pandas as pd
import requests
import streamlit as st


# =========================
# 0. 기본 설정 & Airtable
# =========================

st.set_page_config(
    page_title="아이솔(ISOL) 800x800 매트 견적 프로그램",
    layout="centered",
)

# --- Airtable 설정 (Streamlit secrets 사용) ---
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets.get("AIRTABLE_TABLE_NAME", "Quotes")


def save_to_airtable(data: dict):
    """견적 데이터를 Airtable에 1건 저장"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"records": [{"fields": data}]}
    res = requests.post(url, json=payload, headers=headers)
    return res.status_code, res.json()


# =========================
# 1. 공통 유틸 (로고/스타일)
# =========================

def get_base64_of_file(path: str):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None


def inject_global_css():
    logo_b64 = get_base64_of_file("isollogo.png")

    css = """
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif;
    }
    .isol-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .isol-subtitle {
        font-size: 0.95rem;
        color: #7a8a9a;
    }
    .isol-section-title {
        font-weight: 700;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .quote-box {
        border-radius: 10px;
        padding: 1rem 1.2rem;
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        margin-top: 1rem;
        position: relative;
    }
    .quote-box h3 {
        margin-top: 0;
    }
    .result-highlight {
        background: #e6fffa;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-top: 0.8rem;
        border: 1px solid #b2f5ea;
    }
    .stButton>button {
        border-radius: 999px;
        padding: 0.4rem 1.4rem;
        font-weight: 600;
    }
    .login-card {
        border-radius: 16px;
        padding: 1.8rem 1.6rem;
        border: 1px solid #e2e8f0;
        background: #ffffffaa;
        backdrop-filter: blur(6px);
    }
    .print-area {
        position: relative;
        padding: 1.5rem;
        border-radius: 10px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        margin-top: 1.5rem;
    }
    .print-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    </style>
    """

    # 워터마크 (오른쪽 하단)
    if logo_b64:
        watermark_css = f"""
        <style>
        .print-area::after {{
            content: "";
            position: absolute;
            right: 20px;
            bottom: 20px;
            width: 120px;
            height: 120px;
            background-image: url("data:image/png;base64,{logo_b64}");
            background-size: contain;
            background-repeat: no-repeat;
            opacity: 0.08;
            pointer-events: none;
        }}
        </style>
        """
        css += watermark_css

    st.markdown(css, unsafe_allow_html=True)


def show_top_logo():
    logo_b64 = get_base64_of_file("isollogo.png")
    if not logo_b64:
        st.markdown(
            "<h2 style='text-align:center;color:#3b82f6;'>ISOL</h2>",
            unsafe_allow_html=True,
        )
        return

    html = f"""
    <div class="isol-header">
        <img src="data:image/png;base64,{logo_b64}" style="height:60px; margin-bottom:0.5rem;" />
        <div style="font-size:1.6rem;font-weight:800;color:#1f2933;">아이솔(ISOL)</div>
        <div class="isol-subtitle">800×800 매트 견적 프로그램 · 간편측정 · 실제측정 기반 프리미엄 매트 산출</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# =========================
# 2. 계산 로직
# =========================

MATERIAL_PRICES = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}

INSTALL_COST_PER_MAT = 6400
VAT_RATE = 0.10


def pyeong_simple_mats(pyeong: float, area_mode: str, expanded: bool) -> int:
    """간편측정: 평형 + 시공범위로 대략 매트 장수 계산"""
    factors = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0,
    }
    factor = factors.get(area_mode, 0.93)
    base = pyeong * factor

    if not expanded:
        base = max(0, base - 8)  # 비확장형은 8장 감산

    # 넉넉하게 10% 여유
    mats = math.ceil(base * 1.10)
    return max(mats, 0)


def custom_round_0_3_0_6(x: float) -> float:
    """0.3 이하는 버림, 0.6 이상은 올림, 그 사이(0.3~0.6 미만)는 0.5단위"""
    if x <= 0:
        return 0.0
    i = int(x)
    f = x - i
    if f < 0.3:
        return float(i)
    elif f < 0.6:
        return i + 0.5
    else:
        return float(i + 1)


def detailed_mats(regions: dict) -> int:
    """
    실제측정: 각 구역별 (가로/세로 cm) dict를 받아 매트 장수 계산
    regions = {
        "거실": {"w": 350, "h": 500},
        ...
    }
    """
    total = 0.0
    for name, dims in regions.items():
        w = dims.get("w", 0)
        h = dims.get("h", 0)
        if w <= 0 or h <= 0:
            continue
        count_w = custom_round_0_3_0_6(w / 80.0)
        count_h = custom_round_0_3_0_6(h / 80.0)
        mats = count_w * count_h
        total += mats

    # 전체 장수에도 10% 여유
    return math.ceil(total * 1.10)


def calculate_price(total_mats: int, material: str):
    unit_price = MATERIAL_PRICES.get(material, 39000)
    material_cost = total_mats * unit_price
    install_cost = total_mats * INSTALL_COST_PER_MAT
    subtotal = material_cost + install_cost
    final = int(round(subtotal * (1 + VAT_RATE)))
    return unit_price, material_cost, install_cost, subtotal, final


# =========================
# 3. 로그인 화면
# =========================

def login_screen():
    inject_global_css()
    show_top_logo()

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("🔐 아이솔(ISOL) 견적 시스템 로그인")
    st.caption("승인된 사용자만 접근할 수 있습니다.")

    col1, col2 = st.columns(2)
    with col1:
        user_id = st.text_input("아이디", value="", placeholder="isol_admin")
    with col2:
        password = st.text_input("비밀번호", type="password", placeholder="********")

    login_btn = st.button("로그인", type="primary")

    if login_btn:
        if user_id == "isol_admin" and password == "isol202512!":
            st.session_state["logged_in"] = True
            st.success("로그인 성공!")
            st.experimental_rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# 4. 메인 견적 페이지
# =========================

ROOM_NAMES = [
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


def main_app():
    inject_global_css()
    show_top_logo()

    st.markdown('<div class="isol-section-title">1. 고객 정보</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input("고객명")
    with col2:
        phone_number = st.text_input("연락처 (숫자만 또는 '-' 포함)")

    address = st.text_input("주소 (직접 입력 또는 외부 검색 후 복사)")
    install_date = st.date_input("시공 희망일", value=date.today())

    memo = st.text_area("고객 메모 / 특이사항", height=60)

    st.markdown('<div class="isol-section-title">2. 계산 설정</div>', unsafe_allow_html=True)

    calc_mode = st.radio("계산 모드 선택", ["간편측정", "실제측정"], horizontal=True)

    material_type = st.selectbox("매트 재질 선택", list(MATERIAL_PRICES.keys()))

    total_mats = 0
    area_option_text = ""

    # ------------- 간편측정 -------------
    if calc_mode == "간편측정":
        st.info("평수와 시공 범위를 기준으로 평균 장수를 계산합니다. (±10% 편차 가능)")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            pyeong = st.number_input("평수 입력", min_value=1.0, step=0.5)
        with col_b:
            area_option = st.selectbox(
                "시공 범위",
                ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"],
            )
        with col_c:
            expanded = st.selectbox("확장형 여부", ["확장형", "비확장형"]) == "확장형"

        area_option_text = area_option
        total_mats = pyeong_simple_mats(pyeong, area_option, expanded)

    # ------------- 실제측정 -------------
    else:
        st.info("각 구역별 실제 가로/세로(cm)를 입력합니다. 0.3 이하는 버림, 0.6 이상은 올림 규칙을 적용합니다.")
        regions = {}
        for room in ROOM_NAMES:
            with st.expander(f"{room} 실측 입력", expanded=(room == "거실")):
                c1, c2 = st.columns(2)
                with c1:
                    w = st.number_input(f"{room} 가로(cm)", min_value=0.0, step=10.0, key=f"{room}_w")
                with c2:
                    h = st.number_input(f"{room} 세로(cm)", min_value=0.0, step=10.0, key=f"{room}_h")
                if w > 0 and h > 0:
                    regions[room] = {"w": w, "h": h}

        area_option_text = "실제측정"
        total_mats = detailed_mats(regions)

    st.markdown('<div class="isol-section-title">3. 견적 산출</div>', unsafe_allow_html=True)

    if total_mats <= 0:
        st.warning("계산에 필요한 값이 부족합니다. 입력값을 확인해 주세요.")
        return

    unit_price, material_cost, install_cost, subtotal, final_total = calculate_price(
        total_mats, material_type
    )

    # 견적번호 & 날짜
    now = datetime.now()
    quote_date_str = now.strftime("%Y.%m.%d %H:%M")
    quote_id = f"Q-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

    # ------- 출력 박스 -------
    st.markdown('<div class="print-area">', unsafe_allow_html=True)
    st.markdown('<div class="print-title">아이솔(ISOL) 매트 견적서</div>', unsafe_allow_html=True)

    st.write(f"**일련번호:** {quote_id}")
    st.write(f"**견적일자:** {quote_date_str}")

    st.write("---")
    st.write("#### 고객 정보")
    st.write(f"- 고객명: {customer_name}")
    st.write(f"- 연락처: {phone_number}")
    st.write(f"- 주소: {address}")
    st.write(f"- 시공 희망일: {install_date.strftime('%Y-%m-%d')}")

    st.write("#### 시공 / 제품 정보")
    st.write(f"- 계산 방식: {calc_mode}")
    if calc_mode == "간편측정":
        st.write(f"- 시공 범위: {area_option_text}")
    else:
        st.write("- 시공 범위: 실제측정 (구역별 실측값 기준)")
    st.write(f"- 매트 재질: {material_type}")
    st.write(f"- 총 필요 매트 수: **{total_mats}장**")

    st.write("#### 금액 상세")
    st.write(f"- 매트 단가: {unit_price:,.0f} 원/장")
    st.write(f"- 재료비: {material_cost:,.0f} 원")
    st.write(f"- 시공비 (장당 {INSTALL_COST_PER_MAT:,.0f}원): {install_cost:,.0f} 원")
    st.write(f"- 합계 (VAT 전): {subtotal:,.0f} 원")

    st.markdown(
        f"<div class='result-highlight'>최종 견적 (VAT 10% 포함): "
        f"<strong>{final_total:,.0f} 원</strong></div>",
        unsafe_allow_html=True,
    )

    if memo:
        st.write("#### 메모")
        st.write(memo)

    st.markdown("</div>", unsafe_allow_html=True)  # print-area 끝

    st.caption("※ 실제 시공 환경에 따라 ±10% 수준의 차이가 발생할 수 있습니다.")

    # =====================
    # Airtable 저장 + 버튼
    # =====================
    st.write("")
    save_btn = st.button("💾 견적 기록 저장 (Airtable)")

    if save_btn:
        record = {
            "Quote ID": quote_id,
            "Created Date": now.strftime("%Y-%m-%d %H:%M"),
            "Customer Name": customer_name,
            "Phone Number": phone_number,
            "Address Details": address,
            "Installation Date": install_date.strftime("%Y-%m-%d"),
            "Calculation Mode": calc_mode,
            "Material Type": material_type,
            "Area Option": area_option_text,
            "Total Materials": total_mats,
            "Material Cost": material_cost,
            "Install Cost": install_cost,
            "Final Total (VAT)": final_total,
            "Memo": memo,
        }

        status, res = save_to_airtable(record)
        if status in (200, 201):
            st.success("Airtable에 견적 기록이 저장되었습니다.")
        else:
            st.error(f"Airtable 저장 실패: {res}")

    st.write("")
    st.info("🖨 견적서 출력은 브라우저 인쇄 기능(Ctrl+P)을 사용하세요. (워터마크 자동 포함)")


# =========================
# 5. 진입점
# =========================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    main_app()
