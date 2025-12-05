import streamlit as st
import math
import base64
from datetime import date

# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="견적프로그램",
    layout="centered",
)


# --------------------------------------------------------
# 로고 함수
# --------------------------------------------------------
def get_base64(bin_file: str) -> str:
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()


def show_logo_top():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style='text-align:center; margin:0;'>
                <img src='data:image/png;base64,{logo}' width='130'>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except:
        st.error("⚠ isollogo.png 파일이 없습니다. app.py와 같은 폴더에 넣어주세요.")


# --------------------------------------------------------
# 장수 계산 공식 (공통)
# --------------------------------------------------------
def mats_from_area(total_area_cm2: float, mat_side_cm: float) -> int:
    if total_area_cm2 <= 0:
        return 0

    mat_area = mat_side_cm * mat_side_cm
    raw = total_area_cm2 / mat_area

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
# 평수 기반 장수 계산
# --------------------------------------------------------
def simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm):
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0,
    }

    mats_800 = pyeong * factor_800[area_type]
    base_area = mats_800 * (80 ** 2)

    mats = mats_from_area(base_area, mat_side_cm)

    # 800×800인 경우만 -8장 규칙 적용
    if expand_type == "비확장형" and mat_side_cm == 80:
        mats -= 8

    return max(mats, 0)


# --------------------------------------------------------
# 견적서 HTML 생성
# --------------------------------------------------------
def render_estimate(
    name, phone, addr, detail_addr, install_date,
    material_type, mat_size, total_mats,
    unit_price, install_cost_per_mat, final_price,
    material_cost, install_cost, supply_total, vat_amount
):
    return f"""
    <div id="printArea" style="
        font-family:pretendard, sans-serif;
        padding:25px;
        border-radius:12px;
        background:#eef2f7;
        color:#222;
    ">
        <h2 style="text-align:center; color:#2c6dd5;">견적서</h2>

        <h4>■ 고객 정보</h4>
        고객명: {name}<br>
        연락처: {phone}<br>
        주소: {addr} {detail_addr}<br>
        시공희망일: {install_date}<br><br>

        <h4>■ 시공 내용</h4>
        매트 재질: {material_type}<br>
        매트 크기: {mat_size}<br>
        필요 매트 수량: {total_mats} 장<br><br>

        <h4>■ 비용 내역</h4>
        재료비 (공급가): {material_cost:,} 원<br>
        시공비 (공급가): {install_cost:,} 원<br>
        공급가 합계: {supply_total:,} 원<br>
        부가세 10%: {vat_amount:,} 원<br>
        <b>최종 견적 (VAT 포함): {final_price:,} 원</b><br>
    </div>

    <script>
        function printPage() {{
            var content = document.getElementById('printArea').innerHTML;
            var myWindow = window.open('', '', 'width=900,height=900');
            myWindow.document.write(`
                <html>
                <head>
                    <title>견적서</title>
                </head>
                <body style="font-family:pretendard, sans-serif; padding:20px;">
                    ${content}
                </body>
                </html>
            `);
            myWindow.document.close();
            myWindow.focus();
            myWindow.print();
        }}
    </script>

    <button onclick="printPage()"
        style="margin-top:15px; padding:12px 24px;
               background:#2c6dd5; color:white; border:none;
               border-radius:8px; font-size:16px; cursor:pointer;">
        🖨 인쇄하기
    </button>
    """


# --------------------------------------------------------
# 로그인 화면
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown("<h1 style='text-align:center;'>견적프로그램</h1>", unsafe_allow_html=True)

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("로그인 정보가 올바르지 않습니다.")


# --------------------------------------------------------
# 메인 프로그램
# --------------------------------------------------------
def calculator():
    show_logo_top()
    st.markdown("<h1 style='text-align:center;'>견적프로그램</h1>", unsafe_allow_html=True)

    # 고객 정보
    st.subheader("🧾 고객 정보")
    name = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    detail_addr = st.text_input("상세주소")
    install_date = st.date_input("시공희망일", value=date.today())

    # 재질 선택
    st.subheader("📌 매트 재질 선택")
    material_type = st.selectbox("원단 재질 선택", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])

    base_price_800 = {"일반 TPU": 39000, "프리미엄 TPU": 42000, "패브릭 TPU": 50000}

    # 매트 크기 선택
    st.subheader("📌 매트 크기 선택")
    mat_size = st.selectbox("매트 크기 선택", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])
    side_mm = int(mat_size.split("×")[0])
    mat_side_cm = side_mm / 10.0

    # 계산모드
    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox("범위 선택", ["거실","거실+복도","거실+복도+아이방1","거실+복도+주방"])
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기", key="simple"):
            total_mats = simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm)
            st.success(f"필요 매트 수량: {total_mats}장")

    else:
        st.subheader("📏 실측 입력")
        zones = ["거실","복도","아일랜드","주방","안방","아이방1","아이방2","아이방3","알파룸"]

        total_area = 0
        for z in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{z} 가로(cm)", min_value=0.0)
            h = col2.number_input(f"{z} 세로(cm)", min_value=0.0)
            if w > 0 and h > 0:
                total_area += w * h

        if st.button("계산하기", key="real"):
            total_mats = mats_from_area(total_area, mat_side_cm)
            st.success(f"필요 매트 수량: {total_mats}장")

    # ---------------- 견적서 ----------------
    if total_mats > 0:
        st.subheader("📄 견적서")

        # 단가 계산
        base_price = base_price_800[material_type]
        area_ratio = (side_mm * side_mm) / (800 * 800)
        unit_price = int(round((base_price * area_ratio) / 500) * 500)

        # 시공비 계산
        front_num = side_mm // 100
        install_cost_per_mat = front_num * side_mm

        # 공급가 계산
        material_cost = unit_price * total_mats
        install_cost = install_cost_per_mat * total_mats
        supply_total = material_cost + install_cost
        vat_amount = int(supply_total * 0.10)
        final_price = supply_total + vat_amount

        estimate_html = render_estimate(
            name, phone, addr, detail_addr, install_date,
            material_type, mat_size, total_mats,
            unit_price, install_cost_per_mat, final_price,
            material_cost, install_cost, supply_total, vat_amount
        )

        st.markdown(estimate_html, unsafe_allow_html=True)


# --------------------------------------------------------
# 실행 제어
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
else:
    calculator()
