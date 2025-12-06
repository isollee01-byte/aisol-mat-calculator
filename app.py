import streamlit as st
import math
import base64
import datetime
import uuid

# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(page_title="견적프로그램", layout="centered")

# --------------------------------------------------------
# 로고 표시 함수
# --------------------------------------------------------
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"<div style='text-align:center; margin-bottom:15px;'><img src='data:image/png;base64,{logo}' width='130'></div>",
            unsafe_allow_html=True,
        )
    except:
        st.warning("로고 파일(isollogo.png)을 찾을 수 없습니다.")

# --------------------------------------------------------
# 장수 계산 함수
# --------------------------------------------------------
def mats_from_area(area_cm2, mat_side_cm):
    if area_cm2 <= 0: return 0

    mat_area = mat_side_cm * mat_side_cm
    raw = area_cm2 / mat_area

    frac = raw - int(raw)
    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    mats = int(mats * 1.10)
    return max(mats, 0)

# --------------------------------------------------------
# 평수 기반 간편측정
# --------------------------------------------------------
def simple_mode_calc(pyeong, area_type, expand, mat_cm):
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0,
    }

    mats_800 = pyeong * factor_800[area_type]
    base_area = mats_800 * (80 ** 2)

    mats = mats_from_area(base_area, mat_cm)

    if expand == "비확장형":
        mats -= 8

    return max(mats, 0)

# --------------------------------------------------------
# 인쇄용 견적서 HTML 생성 (A안) — ※★ 수정된 부분: serial_no 추가 ★※
# --------------------------------------------------------
def build_estimate_html(
    serial_no,   # ← 추가됨
    name, phone, addr, detail, install_date,
    material, size, mats,
    material_cost, install_cost, total_cost
):

    html = f"""
<html>
<head>
<meta charset="UTF-8">
<title>견적서</title>

<style>
body {{
    font-family: 'Noto Sans KR', sans-serif;
    padding: 40px;
}}
.section {{
    border: 1px solid #d9d9d9;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
}}
.title {{
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 10px;
}}
.row {{
    margin: 5px 0;
}}
.value {{
    font-weight: bold;
}}
</style>

</head>
<body>

<h1 style="text-align:center; color:#1E88E5;">견적서</h1>

<div class="section">
    <div class="title">■ 고객 정보</div>
    <div class="row">견적번호: <span class="value">{serial_no}</span></div>
    <div class="row">고객명: <span class="value">{name}</span></div>
    <div class="row">연락처: <span class="value">{phone}</span></div>
    <div class="row">주소: <span class="value">{addr} {detail}</span></div>
    <div class="row">시공희망일: <span class="value">{install_date}</span></div>
</div>

<div class="section">
    <div class="title">■ 시공 내용</div>
    <div class="row">매트 재질: <span class="value">{material}</span></div>
    <div class="row">매트 크기: <span class="value">{size}</span></div>
    <div class="row">필요 매트 수량: <span class="value">{mats} 장</span></div>
</div>

<div class="section">
    <div class="title">■ 비용 내역</div>
    <div class="row">재료비: <span class="value">{material_cost:,} 원</span></div>
    <div class="row">시공비: <span class="value">{install_cost:,} 원</span></div>
    <div class="row" style="margin-top:15px; font-size:18px;">
        최종 견적(VAT 포함): <span class="value">{total_cost:,} 원</span>
    </div>
</div>

<script>
window.onload = function() {{
    window.print();
}}
</script>

</body>
</html>
"""
    return html

# --------------------------------------------------------
# 로그인 화면
# --------------------------------------------------------
def login_page():
    show_logo()
    st.markdown("<h2 style='text-align:center;'>견적프로그램</h2>", unsafe_allow_html=True)

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("로그인 정보가 올바르지 않습니다.")

# --------------------------------------------------------
# 메인 계산기 — ※★ serial_no 생성 추가 ★※
# --------------------------------------------------------
def calculator():
    show_logo()
    st.markdown("<h2 style='text-align:center;'>견적프로그램</h2>", unsafe_allow_html=True)

    st.subheader("고객 정보")
    name = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    detail = st.text_input("상세 주소")
    install_date = st.date_input("시공 희망일")

    st.subheader("매트 선택")
    material = st.selectbox("재질", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])
    size = st.selectbox("크기", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])

    side_mm = int(size.split("×")[0])
    mat_cm = side_mm / 10

    mat_unit_price = {
        "일반 TPU": {600: 35000, 700: 42000, 800: 50000, 1000: 78000, 1200: 98000},
        "프리미엄 TPU": {600: 38000, 700: 45000, 800: 53000, 1000: 82000, 1200: 103000},
        "패브릭 TPU": {600: 45000, 700: 52000, 800: 60000, 1000: 90000, 1200: 120000},
    }

    install_unit = {
        600: 3600, 700: 4900, 800: 6400, 1000: 10000, 1200: 14400
    }

    price_mat = mat_unit_price[material][side_mm]
    price_install = install_unit[side_mm]

    st.subheader("계산모드")
    mode = st.selectbox("선택", ["간편측정", "실제측정"])

    mats = 0

    if mode == "간편측정":
        p = st.number_input("평수", min_value=1)
        area_type = st.selectbox("범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand = st.selectbox("확장여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            mats = simple_mode_calc(p, area_type, expand, mat_cm)
            st.success(f"총 매트 수량: {mats} 장")

    else:
        st.subheader("실측 입력")
        zones = ["거실", "복도", "주방", "안방", "아이방1", "아이방2"]

        area = 0
        for z in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{z} 가로(cm)", min_value=0.0)
            h = col2.number_input(f"{z} 세로(cm)", min_value=0.0)
            area += w * h

        if st.button("계산하기"):
            mats = mats_from_area(area, mat_cm)
            st.success(f"총 매트 수량: {mats} 장")

    if mats > 0:
        material_cost = mats * price_mat
        install_cost = mats * price_install
        total_cost = int((material_cost + install_cost) * 1.10)

        st.subheader("견적 결과")
        st.info(f"재료비: {material_cost:,} 원")
        st.info(f"시공비: {install_cost:,} 원")
        st.success(f"최종 견적(VAT 포함): {total_cost:,} 원")

        # ★ 견적번호 생성 추가 ★
        serial_no = "ISOL-" + datetime.date.today().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6]

        html = build_estimate_html(
            serial_no,
            name, phone, addr, detail, install_date,
            material, size, mats,
            material_cost, install_cost, total_cost
        )

        b64 = base64.b64encode(html.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="estimate.html" target="_blank">📄 견적서 인쇄하기</a>'

        st.markdown(href, unsafe_allow_html=True)

# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_page()
else:
    calculator()
