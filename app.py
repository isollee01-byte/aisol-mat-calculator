import streamlit as st
import math
import base64
from datetime import datetime


# --------------------------------------------------------
# 기본 설정
# --------------------------------------------------------
st.set_page_config(
    page_title="견적프로그램",
    layout="centered",
)


# --------------------------------------------------------
# 로고 처리
# --------------------------------------------------------
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()


def show_logo():
    try:
        logo_code = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:8px;">
                <img src="data:image/png;base64,{logo_code}" width="120">
            </div>
            """,
            unsafe_allow_html=True,
        )
    except:
        st.warning("⚠ isollogo.png 파일이 없습니다.")


# --------------------------------------------------------
# 가격표(사이즈별 단가 적용)
# --------------------------------------------------------
PRICE_TABLE = {
    "일반 TPU":   {600:22000, 700:30000, 800:39000, 1000:61000, 1200:88000},
    "프리미엄 TPU": {600:24000, 700:32000, 800:42000, 1000:66000, 1200:94000},
    "패브릭 TPU":   {600:28000, 700:38000, 800:50000, 1000:78000, 1200:112000},
}


# --------------------------------------------------------
# 시공비 계산 (앞자리 × mm)
# --------------------------------------------------------
def get_install_cost(side_mm):
    front = side_mm // 100
    return front * side_mm


# --------------------------------------------------------
# 장수 계산
# --------------------------------------------------------
def calc_mats(total_area_cm2, side_cm):
    if total_area_cm2 <= 0:
        return 0

    mat_area = side_cm * side_cm
    raw = total_area_cm2 / mat_area

    frac = raw - int(raw)

    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    return max(int(mats * 1.10), 1)


# --------------------------------------------------------
# 평형계수(800×800 기준)
# --------------------------------------------------------
FACTOR_800 = {
    "거실": 0.93,
    "거실+복도": 1.46,
    "거실+복도+아이방1": 1.67,
    "거실+복도+주방": 2.00,
}


def calc_simple(pyeong, area_type, expand_type, side_cm):
    m800 = pyeong * FACTOR_800[area_type]
    total_area = m800 * (80 * 80)
    mats = calc_mats(total_area, side_cm)

    if expand_type == "비확장형" and side_cm == 80:
        mats = max(mats - 8, 1)

    return mats


# --------------------------------------------------------
# 견적서 HTML 생성 (A안)
# --------------------------------------------------------
def build_estimate_html(
    serial_no, name, phone, addr, date,
    material, size, mats, mat_cost, install_cost, total_cost
):
    logo = get_base64("isollogo.png")

    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial;
                padding: 40px;
            }}
            .title {{
                text-align:center;
                font-size:28px;
                margin-bottom:20px;
                font-weight:700;
                color:#1A3C8E;
            }}
            .box {{
                border:1px solid #ddd;
                padding:15px;
                border-radius:10px;
                background:#f4f8ff;
                margin-bottom:20px;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
                margin-top:20px;
            }}
            th, td {{
                border:1px solid #bbb;
                padding:10px;
            }}
            th {{
                background:#eaf1ff;
            }}
            .total {{
                font-size:20px;
                font-weight:700;
            }}
        </style>
    </head>

    <body>

        <div style="text-align:center;">
            <img src="data:image/png;base64,{logo}" width="110">
        </div>

        <div class="title">아이솔(ISOL) 매트 견적서</div>

        <div class="box">
            <h3>고객 정보</h3>
            고객명: {name}<br>
            연락처: {phone}<br>
            주소: {addr}<br>
            시공 희망일: {date}<br>
            견적번호: {serial_no}
        </div>

        <div class="box">
            <h3>매트 정보</h3>
            재질: {material}<br>
            사이즈: {size}<br>
            필요 수량: {mats:,} 장
        </div>

        <table>
            <tr><th>항목</th><th>금액</th></tr>
            <tr><td>재료비</td><td>{mat_cost:,} 원</td></tr>
            <tr><td>시공비</td><td>{install_cost:,} 원</td></tr>
            <tr><td class="total">최종 견적(VAT 포함)</td><td class="total">{total_cost:,} 원</td></tr>
        </table>

        <script>
            window.onload = function() {{
                window.print();
            }};
        </script>

    </body>
    </html>
    """


# --------------------------------------------------------
# 메인
# --------------------------------------------------------
def main():
    show_logo()
    st.markdown("<h1 style='text-align:center;'>견적프로그램</h1>", unsafe_allow_html=True)

    # 고객 정보
    st.subheader("🧾 고객 정보")
    name = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    detail = st.text_input("상세주소")
    install_date = st.date_input("시공 희망일")

    # 재질 선택
    st.subheader("📌 매트 재질 선택")
    material = st.selectbox("재질", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])

    # 사이즈 선택
    st.subheader("📌 매트 크기 선택")
    size_str = st.selectbox("사이즈", ["600×600","700×700","800×800","1000×1000","1200×1200"])

    side_mm = int(size_str.split("×")[0])
    side_cm = side_mm / 10

    unit_price = PRICE_TABLE[material][side_mm]
    install_unit = get_install_cost(side_mm)

    # 계산 모드
    st.subheader("📌 계산 모드")
    mode = st.selectbox("방식", ["간편측정", "실제측정"])

    mats = 0

    if mode == "간편측정":
        p = st.number_input("평수 입력", min_value=1)
        area = st.selectbox("범위", list(FACTOR_800.keys()))
        exp = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            mats = calc_simple(p, area, exp, side_cm)
            st.success(f"필요 수량: {mats} 장")

    else:
        st.subheader("실측 입력 (cm)")
        zones = ["거실","복도","아일랜드","주방","안방","아이방1","아이방2","아이방3","알파룸"]
        total_area = 0
        for z in zones:
            c1,c2 = st.columns(2)
            w = c1.number_input(f"{z} 가로(cm)", min_value=0.0)
            h = c2.number_input(f"{z} 세로(cm)", min_value=0.0)
            total_area += w*h

        if st.button("계산하기"):
            mats = calc_mats(total_area, side_cm)
            st.success(f"필요 수량: {mats} 장")

    # 견적 출력
    if mats > 0:
        mat_cost = mats * unit_price
        install_cost = mats * install_unit
        total_cost = int((mat_cost + install_cost) * 1.10)

        st.subheader("📄 견적 결과")
        st.write(f"재료비: **{mat_cost:,} 원**")
        st.write(f"시공비: **{install_cost:,} 원**")
        st.write(f"최종 견적(VAT 포함): **{total_cost:,} 원**")

        serial = f"ISOL-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"

        # 견적서 보기 버튼 -> 인쇄 전용 페이지 렌더링
        if st.button("🖨 견적서 인쇄"):
            html = build_estimate_html(
                serial, name, phone,
                addr + " " + detail,
                install_date,
                material, size_str,
                mats, mat_cost, install_cost, total_cost
            )

            st.markdown(html, unsafe_allow_html=True)


main()
