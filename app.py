import streamlit as st
import math
import base64
import datetime

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
            f"<div style='text-align:center; margin-bottom:14px;'><img src='data:image/png;base64,{logo}' width='130'></div>",
            unsafe_allow_html=True,
        )
    except:
        st.warning("⚠ 로고 파일(isollogo.png)을 찾을 수 없습니다.")


# --------------------------------------------------------
# 매트 장수 계산
# --------------------------------------------------------
def mats_from_area(area_cm2, mat_side_cm):
    if area_cm2 <= 0:
        return 0

    mat_area = mat_side_cm * mat_side_cm
    raw = area_cm2 / mat_area

    frac = raw - int(raw)

    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    mats = int(mats * 1.10)  # +10% 여유량
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
# 견적서 HTML 생성
# --------------------------------------------------------
def build_estimate_html(
    estimate_id, name, phone, addr, detail, install_date,
    material, size, mats,
    material_cost, install_cost, total_cost
):
    today_str = datetime.date.today().strftime("%Y-%m-%d")

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

h1 {{
    text-align: center;
    color: #1E88E5;
    font-size: 30px;
}}

.section {{
    border: 1px solid #d0d0d0;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 22px;
}}

.title {{
    font-size: 19px;
    font-weight: bold;
    margin-bottom: 8px;
}}

.row {{
    font-size: 16px;
    margin: 5px 0;
}}

.value {{
    font-weight: bold;
}}
</style>

</head>
<body>

<h1>견적서</h1>

<div class="section">
    <div class="title">■ 견적 정보</div>
    <div class="row">견적번호: <span class="value">{estimate_id}</span></div>
    <div class="row">작성일: <span class="value">{today_str}</span></div>
</div>

<div class="section">
    <div class="title">■ 고객 정보</div>
    <div class="row">고객명: <span class="value">{name}</span></div>
    <div class="row">연락처: <span class="value">{phone}</span></div>
    <div class="row">주소: <span class="value">{addr} {detail}</span></div>
    <div class="row">시공희망일: <span class="value">{install_date}</span></div>
</div>

<div class="section">
    <div class="title">■ 시공 내용</div>
    <div class="row">재질: <span class="value">{material}</span></div>
    <div class="row">매트 크기: <span class="value">{size}</span></div>
    <div class="row">총 매트 수량: <span class="value">{mats} 장</span></div>
</div>

<div class="section">
    <div class="title">■ 비용 내역</div>
    <div class="row">재료비: <span class="value">{material_cost:,} 원</span></div>
    <div class="row">시공비: <span class="value">{install_cost:,} 원</span></div>
    <div class="row" style="font-size:19px; margin-top:12px;">
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
# 로그인 페이지
# --------------------------------------------------------
def login_page():
    show_logo()
    st.markdown("<h2 style='text-align:center;'>견적프로그램</h2>", unsafe_allow_html=True)

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":

            st.session_state["login"] = True

            today = datetime.date.today().strftime("%Y%m%d")

            if "last_date" not in st.session_state or st.session_state["last_date"] != today:
                st.session_state["counter"] = 1
                st.session_state["last_date"] = today

            st.rerun()
        else:
            st.error("로그인 정보가 올바르지 않습니다.")


# --------------------------------------------------------
# 메인 계산기
# --------------------------------------------------------
def calculator():

    show_logo()
    st.markdown("<h2 style='text-align:center;'>견적프로그램</h2>", unsafe_allow_html=True)

    today = datetime.date.today().strftime("%Y%m%d")
    estimate_id = f"ISOL-{today}-{st.session_state['counter']:03d}"

    # ------------------------------ 고객 정보 ------------------------------
    st.subheader("고객 정보")
    name = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    detail = st.text_input("상세 주소")
    install_date = st.date_input("시공 희망일")

    # ------------------------------ 단가표 ------------------------------
    mat_unit_price = {
        "일반 TPU": {600: 22000, 700: 30000, 800: 39000, 1000: 61000, 1200: 88000},
        "프리미엄 TPU": {600: 24000, 700: 32000, 800: 42000, 1000: 66000, 1200: 94500},
        "패브릭 TPU": {600: 28000, 700: 38500, 800: 50000, 1000: 78000, 1200: 112500},
    }

    install_price = {600: 3600, 700: 4900, 800: 6400, 1000: 10000, 1200: 14400}

    st.subheader("매트 선택")
    material = st.selectbox("재질", list(mat_unit_price.keys()))
    size = st.selectbox("크기", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])

    side_mm = int(size.split("×")[0])
    mat_cm = side_mm / 10

    # ------------------------------ 계산모드 ------------------------------
    st.subheader("계산모드")
    mode = st.selectbox("선택", ["간편측정", "실제측정"])

    mats = 0

    # 간편측정
    if mode == "간편측정":
        p = st.number_input("평수", min_value=1)
        area_type = st.selectbox("범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand = st.selectbox("확장여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            mats = simple_mode_calc(p, area_type, expand, mat_cm)
            st.success(f"총 매트 수량: {mats} 장")

    # 실측
    else:
        st.subheader("실측 입력")
        zones = ["거실", "복도", "주방", "안방", "아이방1", "아이방2"]

        total_area = 0
        for z in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{z} 가로(cm)", min_value=0.0)
            h = col2.number_input(f"{z} 세로(cm)", min_value=0.0)
            total_area += w * h

        if st.button("계산하기"):
            mats = mats_from_area(total_area, mat_cm)
            st.success(f"총 매트 수량: {mats} 장")

    # ------------------------------ 견적 출력 ------------------------------
    if mats > 0:

        price_mat = mat_unit_price[material][side_mm]
        price_install = install_price[side_mm]

        material_cost = mats * price_mat
        install_cost = mats * price_install
        total_cost = int((material_cost + install_cost) * 1.10)

        st.subheader("견적 결과")
        st.info(f"재료비: {material_cost:,} 원")
        st.info(f"시공비: {install_cost:,} 원")
        st.success(f"최종 견적(VAT 포함): {total_cost:,} 원")

        # ------------------------------ 인쇄 기능 복원 ------------------------------
        if st.button("견적서 인쇄하기"):

            html = build_estimate_html(
                estimate_id, name, phone, addr, detail, install_date,
                material, size, mats, material_cost, install_cost, total_cost
            )

            b64 = base64.b64encode(html.encode()).decode()

            print_js = f"""
                <script>
                    var newWin = window.open();
                    newWin.document.write(atob("{b64}"));
                    newWin.document.close();
                </script>
            """

            st.components.v1.html(print_js, height=0, width=0)

            st.session_state["counter"] += 1
            st.rerun()


# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_page()
else:
    calculator()
