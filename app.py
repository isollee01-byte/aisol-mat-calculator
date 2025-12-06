import streamlit as st
import math
import base64
import datetime
import streamlit.components.v1 as components

# =========================================
# 기본 설정
# =========================================
st.set_page_config(page_title="견적프로그램", layout="centered")

# =========================================
# 로고 표시
# =========================================
def get_base64(bin_file):
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def show_logo():
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"<div style='text-align:center; margin-bottom:5px;'><img src='data:image/png;base64,{logo}' width='130'></div>",
            unsafe_allow_html=True
        )
    except:
        st.write("")

# =========================================
# 자동 일련번호 생성
# =========================================
def generate_serial():
    today = datetime.date.today().strftime("%Y%m%d")
    if "serial_counter" not in st.session_state:
        st.session_state["serial_counter"] = 1

    serial = f"ISOL-{today}-{st.session_state['serial_counter']:03d}"
    st.session_state["serial_counter"] += 1
    return serial

# =========================================
# 면적 → 장수 계산
# =========================================
def mats_from_area(area_cm2, mat_side_cm):
    if area_cm2 <= 0:
        return 0

    mat_area = mat_side_cm ** 2
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

# =========================================
# 간편측정 계산
# =========================================
def simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm):

    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.00,
    }

    mats_800 = pyeong * factor_800[area_type]
    base_area = mats_800 * (80 * 80)
    mats = mats_from_area(base_area, mat_side_cm)

    if expand_type == "비확장형":
        mats -= 8

    return max(mats, 0)

# =========================================
# 견적서 HTML (A형 인쇄템플릿)
# =========================================
def build_estimate_html(serial, name, phone, addr, date, material, size, mats, mat_cost, install_cost, total):
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Noto Sans KR', sans-serif;
                padding: 30px;
            }}
            .card {{
                width: 700px;
                margin: auto;
                padding: 30px;
                border-radius: 12px;
                border: 1px solid #d0d7de;
                background: #f8fbff;
            }}
            h2 {{
                color: #0066cc;
                text-align: center;
                margin-bottom: 25px;
            }}
            .section-title {{
                font-size: 17px;
                margin-top: 25px;
                font-weight: bold;
                color: #004a99;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            td {{
                padding: 6px 3px;
                font-size: 15px;
            }}
            .amount {{
                font-weight: bold;
                font-size: 17px;
            }}
        </style>
    </head>

    <body onload="window.print()">
        <div class="card">

            <h2>견적서</h2>

            <div class="section-title">■ 견적 기본 정보</div>
            <table>
                <tr><td>일련번호</td><td>{serial}</td></tr>
                <tr><td>고객명</td><td>{name}</td></tr>
                <tr><td>연락처</td><td>{phone}</td></tr>
                <tr><td>주소</td><td>{addr}</td></tr>
                <tr><td>시공 희망일</td><td>{date}</td></tr>
            </table>

            <div class="section-title">■ 시공 내용</div>
            <table>
                <tr><td>매트 재질</td><td>{material}</td></tr>
                <tr><td>매트 크기</td><td>{size}</td></tr>
                <tr><td>필요 매트 수량</td><td>{mats:,} 장</td></tr>
            </table>

            <div class="section-title">■ 비용</div>
            <table>
                <tr><td>재료비</td><td>{mat_cost:,} 원</td></tr>
                <tr><td>시공비</td><td>{install_cost:,} 원</td></tr>
                <tr><td class="amount">최종 견적(VAT 포함)</td><td class="amount">{total:,} 원</td></tr>
            </table>

        </div>
    </body>
    </html>
    """
    return html

# =========================================
# 메인 계산기
# =========================================
def calculator():
    show_logo()
    st.markdown("<h1 style='text-align:center;'>견적프로그램</h1>", unsafe_allow_html=True)

    st.subheader("🧾 고객 정보")
    name = st.text_input("고객명")
    phone = st.text_input("연락처")
    addr = st.text_input("주소")
    detail = st.text_input("상세주소")
    install_date = st.date_input("시공 희망일")

    st.subheader("📌 매트 재질")
    material = st.selectbox("재질 선택", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])

    price_map = {"일반 TPU": 39000, "프리미엄 TPU": 42000, "패브릭 TPU": 50000}

    st.subheader("📌 매트 크기")
    size = st.selectbox("크기 선택", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])
    side_mm = int(size.split("×")[0])
    mat_side_cm = side_mm / 10
    work_cost_per_mat = (side_mm // 100) * side_mm

    st.subheader("📌 계산 모드")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox("범위 선택", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        expand = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기"):
            total_mats = simple_mode_calc_with_size(pyeong, area_type, expand, mat_side_cm)
            st.success(f"필요 매트 수량: {total_mats} 장")

    else:
        st.subheader("📏 실측 입력")
        zones = ["거실", "복도", "아일랜드", "주방", "안방", "아이방1", "아이방2", "아이방3", "알파룸"]
        total_area = 0

        for z in zones:
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{z} 가로(cm)", min_value=0.0)
            h = col2.number_input(f"{z} 세로(cm)", min_value=0.0)
            total_area += w*h

        if st.button("계산하기"):
            total_mats = mats_from_area(total_area, mat_side_cm)
            st.success(f"실측 매트 수량: {total_mats} 장")

    if total_mats > 0:
        st.subheader("📄 견적 결과")

        mat_cost = total_mats * price_map[material]
        install_cost = total_mats * work_cost_per_mat
        total = int((mat_cost + install_cost) * 1.10)

        st.write(f"재료비: {mat_cost:,} 원")
        st.write(f"시공비: {install_cost:,} 원")
        st.write(f"최종 견적(VAT 포함): {total:,} 원")

        serial_no = generate_serial()

        if st.button("견적서 인쇄하기"):

            html = build_estimate_html(
                serial_no,
                name, phone, addr + " " + detail,
                install_date, material, size,
                total_mats, mat_cost, install_cost, total
            )

            js = f"""
                <script>
                    var win = window.open("", "_blank");
                    win.document.write(`{html}`);
                    win.document.close();
                    win.focus();
                </script>
            """

            components.html(js, height=0, width=0)

# =========================================
# 실행
# =========================================
calculator()
