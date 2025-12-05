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
# 로고 / 워터마크 처리
# --------------------------------------------------------
def get_base64(bin_file: str) -> str:
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()


def show_logo_top():
    """상단 메인 로고"""
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:10px; margin-top:15px;">
                <img src="data:image/png;base64,{logo}" width="130">
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.error("⚠ isollogo.png 파일이 없습니다. app.py와 같은 폴더에 넣어주세요.")


def show_watermark():
    """우측 하단 워터마크 로고"""
    try:
        logo = get_base64("isollogo.png")
        st.markdown(
            f"""
            <div style="
                position: fixed;
                bottom: 25px;
                right: 25px;
                opacity: 0.08;
                z-index: 999;
            ">
                <img src="data:image/png;base64,{logo}" width="160">
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass


# --------------------------------------------------------
# 공통: 면적 → 장수 계산 함수 (cm 기준)
# --------------------------------------------------------
def mats_from_area(total_area_cm2: float, mat_side_cm: float) -> int:
    """
    total_area_cm2 : 전체 바닥 면적 (cm^2)
    mat_side_cm    : 매트 한 변 길이 (cm)  예) 60, 70, 80, 100, 120
    """
    if total_area_cm2 <= 0 or mat_side_cm <= 0:
        return 0

    mat_area = mat_side_cm * mat_side_cm  # 1장 면적 (cm^2)
    raw = total_area_cm2 / mat_area

    if raw <= 0:
        return 0

    frac = raw - int(raw)
    if frac <= 0.3:
        mats = int(raw)
    elif frac >= 0.6:
        mats = int(raw) + 1
    else:
        mats = math.ceil(raw)

    # +10% 여유
    mats = int(mats * 1.10)

    return max(mats, 0)


# --------------------------------------------------------
# 매트 단가 계산 (800×800 기준에서 면적 비례 + 500원 반올림)
# --------------------------------------------------------
BASE_PRICE_800 = {
    "일반 TPU": 39000,
    "프리미엄 TPU": 42000,
    "패브릭 TPU": 50000,
}


def mat_unit_price(material: str, side_mm: int) -> int:
    """
    material : '일반 TPU' 등
    side_mm  : 한 변 길이(mm) 600, 700, 800, 1000, 1200
    """
    base_price = BASE_PRICE_800[material]
    base_area = 80 * 80  # 800mm = 80cm → 80×80 = 6400cm2
    side_cm = side_mm / 10.0
    area = side_cm * side_cm

    raw_price = base_price * (area / base_area)

    # 500원 단위 반올림
    rounded = int(round(raw_price / 500.0) * 500)
    return rounded


def build_price_table_html() -> str:
    """각 재질/사이즈별 단가 표를 HTML 테이블로 생성"""
    sizes = [600, 700, 800, 1000, 1200]
    size_labels = [f"{s}×{s}" for s in sizes]

    header = "<tr><th>재질 / 사이즈</th>" + "".join(
        f"<th>{label}</th>" for label in size_labels
    ) + "</tr>"

    rows = []
    for material in BASE_PRICE_800.keys():
        tds = [f"<td>{material}</td>"]
        for s in sizes:
            price = mat_unit_price(material, s)
            tds.append(f"<td>{price:,.0f}원</td>")
        row_html = "<tr>" + "".join(tds) + "</tr>"
        rows.append(row_html)

    table_html = f"""
    <table style="border-collapse:collapse; width:100%; font-size:0.9rem;">
        {header}
        {''.join(rows)}
    </table>
    """
    return table_html


# --------------------------------------------------------
# 로그인 화면
# --------------------------------------------------------
def login_screen():
    show_logo_top()
    st.markdown(
        """
        <h2 style="text-align:center; margin-bottom:30px;">
            견적프로그램 로그인
        </h2>
        """,
        unsafe_allow_html=True,
    )

    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol25" and pw == "isol202512!":
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")


# --------------------------------------------------------
# 간편측정(평수) 계산
#   - 800×800 기준 예상 장수를 factor로 사용
#   - 이를 면적으로 변환 후, 선택된 매트 사이즈(cm)에 맞춰 다시 계산
#   - 비확장형이면 800×800 기준에서 -8장 조정 후 면적 환산
# --------------------------------------------------------
def simple_mode_calc_with_size(pyeong, area_type, expand_type, mat_side_cm):
    # 800×800 기준 장수 계수
    factor_800 = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2,
    }

    # 800×800 기준 예상 매트 장수
    mats_800 = pyeong * factor_800[area_type]

    # 비확장형이면 800×800 기준에서 -8장
    if expand_type == "비확장형":
        mats_800 = max(mats_800 - 8, 0)

    # 1장 = 80cm × 80cm 기준 면적으로 변환
    base_mat_side_800 = 80  # cm (800mm)
    base_area = mats_800 * (base_mat_side_800 ** 2)  # cm^2

    # 선택된 매트 크기에 맞춰 장수 재계산
    mats = mats_from_area(base_area, mat_side_cm)
    return max(mats, 0)


# --------------------------------------------------------
# 메인 견적 시스템
# --------------------------------------------------------
def calculator():
    show_logo_top()
    show_watermark()

    st.markdown(
        """
        <h1 style="text-align:center; margin-bottom:5px;">
            견적프로그램
        </h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='text-align:center; color:#6B7A90; margin-bottom:25px;'>"
        "TPU / 패브릭 매트 간편 견적 시스템"
        "</p>",
        unsafe_allow_html=True,
    )

    # -----------------------------------
    # 가격표 안내 (옵션)
    # -----------------------------------
    with st.expander("📋 매트 사이즈 / 재질별 1장 단가 보기"):
        st.markdown(
            "<p style='font-size:0.9rem; color:#555;'>"
            "※ 800×800 기준 가격에서 면적 비례 + 500원 단위 반올림으로 산정됩니다."
            "</p>",
            unsafe_allow_html=True,
        )
        st.markdown(build_price_table_html(), unsafe_allow_html=True)

    # -----------------------------------
    # 고객 정보
    # -----------------------------------
    st.subheader("🧾 고객 정보")

    customer_name = st.text_input("고객명")
    customer_phone = st.text_input("연락처")
    selected_address = st.text_input("주소 입력")
    detail_address = st.text_input("상세 주소 입력")
    install_date = st.date_input("시공 희망일", value=date.today())

    # -----------------------------------
    # 매트 재질
    # -----------------------------------
    st.subheader("📌 매트 재질 선택")

    material_type = st.selectbox(
        "원단 재질 선택",
        ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"],
    )

    # -----------------------------------
    # 매트 크기 (mm → cm 변환 + 시공비/장 계산)
    # -----------------------------------
    st.subheader("📌 매트 크기 선택")

    mat_size_str = st.selectbox(
        "매트 크기 선택",
        ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"],
    )

    side_mm = int(mat_size_str.split("×")[0])  # 예: 600, 700, 800 ...
    mat_side_cm = side_mm / 10.0              # 예: 600mm → 60cm

    # 재료비/장
    material_unit_price = mat_unit_price(material_type, side_mm)

    # 시공비/장 = (앞숫자) × (한 변 mm)
    front_number = side_mm // 100
    work_cost_per_mat = front_number * side_mm

    st.markdown(
        f"""
        <div style="font-size:0.9rem; color:#555; margin-top:5px;">
        - 선택된 매트 1장 재료비: <b>{material_unit_price:,.0f}원</b><br>
        - 선택된 매트 1장 시공비: <b>{work_cost_per_mat:,.0f}원</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------
    # 계산 모드 선택
    # -----------------------------------
    st.subheader("📌 계산 모드 선택")
    mode = st.selectbox("모드 선택", ["간편측정", "실제측정"])

    total_mats = 0

    # -------------------------
    # 간편측정 (평수 기반)
    # -------------------------
    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox(
            "범위 선택",
            ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"],
        )
        expand_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

        if st.button("계산하기 (간편)", key="simple_calc"):
            total_mats = simple_mode_calc_with_size(
                pyeong, area_type, expand_type, mat_side_cm
            )
            st.success(f"총 필요 매트 수량: {total_mats}장")

    # -------------------------
    # 실제측정 (고정 구역)
    # -------------------------
    else:
        st.subheader("📏 실측 입력 (필요한 구역만 입력하세요)")

        zones = [
            "거실", "복도", "아일랜드", "주방",
            "안방", "아이방1", "아이방2", "아이방3", "알파룸",
        ]

        total_area_cm2 = 0.0

        for zone in zones:
            st.markdown(f"<b>🏷 {zone}</b>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            w = col1.number_input(f"{zone} 가로(cm)", min_value=0.0, key=f"{zone}_w")
            h = col2.number_input(f"{zone} 세로(cm)", min_value=0.0, key=f"{zone}_h")

            if w > 0 and h > 0:
                total_area_cm2 += (w * h)

        if st.button("계산하기 (실측)", key="precise_calc"):
            total_mats = mats_from_area(total_area_cm2, mat_side_cm)
            st.success(f"총 실측 매트 수량: {total_mats}장")

    # -------------------------
    # 견적 결과 + 견적서
    # -------------------------
    if total_mats > 0:
        st.subheader("📄 견적 결과")

        # 재료비 / 시공비 / 총액
        material_cost = total_mats * material_unit_price
        work_cost = total_mats * work_cost_per_mat
        total_price = int((material_cost + work_cost) * 1.10)  # VAT 포함

        # 견적서 HTML
        quote_html = f"""
        <div id="printArea">
            <div style="
                background:#FFFFFF;
                border-radius:14px;
                padding:24px 22px;
                border:1px solid #D7E5F7;
                box-shadow:0 3px 10px rgba(0,0,0,0.04);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            ">
                <h2 style="text-align:center; color:#2A7DE1; margin-top:0; margin-bottom:18px;">
                    견적서
                </h2>

                <h4 style="margin-bottom:8px; color:#1F2933;">■ 고객 정보</h4>
                <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
                    <tr><td style="width:28%; padding:4px 0; color:#555;">고객명</td>
                        <td style="padding:4px 0;"><b>{customer_name}</b></td></tr>
                    <tr><td style="padding:4px 0; color:#555;">연락처</td>
                        <td style="padding:4px 0;">{customer_phone}</td></tr>
                    <tr><td style="padding:4px 0; color:#555;">주소</td>
                        <td style="padding:4px 0;">{selected_address} {detail_address}</td></tr>
                    <tr><td style="padding:4px 0; color:#555;">시공 희망일</td>
                        <td style="padding:4px 0;">{install_date}</td></tr>
                </table>

                <div style="height:10px;"></div>

                <h4 style="margin-bottom:8px; color:#1F2933;">■ 시공 내용</h4>
                <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
                    <tr><td style="width:28%; padding:4px 0; color:#555;">매트 재질</td>
                        <td style="padding:4px 0;">{material_type}</td></tr>
                    <tr><td style="padding:4px 0; color:#555;">매트 크기</td>
                        <td style="padding:4px 0;">{mat_size_str}</td></tr>
                    <tr><td style="padding:4px 0; color:#555;">필요 매트 수량</td>
                        <td style="padding:4px 0;">{total_mats:,} 장</td></tr>
                </table>

                <div style="height:10px;"></div>

                <h4 style="margin-bottom:8px; color:#1F2933;">■ 비용 내역</h4>
                <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
                    <tr><td style="width:28%; padding:4px 0; color:#555;">재료비</td>
                        <td style="padding:4px 0;">{material_cost:,.0f} 원</td></tr>
                    <tr><td style="padding:4px 0; color:#555;">시공비</td>
                        <td style="padding:4px 0;">{work_cost:,.0f} 원</td></tr>
                    <tr><td style="padding:6px 0; color:#111;"><b>최종 견적(VAT 포함)</b></td>
                        <td style="padding:6px 0;"><b>{total_price:,.0f} 원</b></td></tr>
                </table>
            </div>
        </div>
        """

        st.markdown(quote_html, unsafe_allow_html=True)

        # 인쇄 버튼 (프린터 이모지 제거, 텍스트만)
        st.markdown(
            """
            <script>
                function printQuote() {
                    const printContents = document.getElementById('printArea').innerHTML;
                    const originalContents = document.body.innerHTML;
                    document.body.innerHTML = printContents;
                    window.print();
                    document.body.innerHTML = originalContents;
                    location.reload();
                }
            </script>
            <button onclick="printQuote()"
                style="
                    margin-top:14px;
                    padding:10px 22px;
                    border:none;
                    border-radius:8px;
                    background:#2A7DE1;
                    color:white;
                    font-size:0.95rem;
                    cursor:pointer;
                ">
                견적서 인쇄
            </button>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------------
# 실행 (로그인 제어)
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login_screen()
    st.stop()
else:
    calculator()