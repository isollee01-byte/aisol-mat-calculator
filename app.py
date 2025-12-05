import streamlit as st
import math
import base64
from datetime import datetime

st.set_page_config(page_title="매트 견적 시스템", layout="centered")

# --------------------------------------------------------
# 로고 Base64
# --------------------------------------------------------
def load_logo_base64():
    try:
        with open("isollogo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

LOGO_B64 = load_logo_base64()


# --------------------------------------------------------
# 로그인
# --------------------------------------------------------
def login():
    st.markdown("<h2 style='text-align:center;'>아이솔 매트 견적 시스템</h2>", unsafe_allow_html=True)
    user = st.text_input("아이디")
    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if user == "isol2025" and pw == "isol202512!":
            st.session_state["login"] = True
        else:
            st.error("로그인 정보가 올바르지 않습니다.")


# --------------------------------------------------------
# 면적 함수
# --------------------------------------------------------
def mat_area(size_str):
    w, h = size_str.split("×")
    return (int(w)/1000) * (int(h)/1000)


# --------------------------------------------------------
# 비확장 감산
# --------------------------------------------------------
def non_expand_deduction(size_str):
    lost_area = 0.64 * 8
    area_per_mat = mat_area(size_str)
    deduction = lost_area / area_per_mat
    return max(int(round(deduction)), 0)


# --------------------------------------------------------
# 간편측정
# --------------------------------------------------------
def simple_calc(pyeong, area_type, extend_type, size_str):
    factors = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0
    }

    mats = pyeong * factors[area_type]

    if mats - int(mats) <= 0.3:
        mats = int(mats)
    elif mats - int(mats) >= 0.6:
        mats = int(mats) + 1
    else:
        mats = math.ceil(mats)

    mats = int(mats * 1.10)

    if extend_type == "비확장형":
        mats -= non_expand_deduction(size_str)

    return max(mats, 0)


# --------------------------------------------------------
# 정밀측정
# --------------------------------------------------------
def precision_calc(measures, extend_type, size_str):
    total = 0

    for w, h in measures:
        row = w / int(size_str.split("×")[0])
        col = h / int(size_str.split("×")[1])
        total += math.ceil(row) * math.ceil(col)

    if extend_type == "비확장형":
        total -= non_expand_deduction(size_str)

    return max(total, 0)


# --------------------------------------------------------
# 메인 페이지
# --------------------------------------------------------
def main():
    st.markdown("<h1 style='text-align:center;'>매트 견적 시스템</h1>", unsafe_allow_html=True)

    customer = st.text_input("고객명")
    phone = st.text_input("연락처")
    address = st.text_input("주소")
    date = st.date_input("시공 희망일")

    mode = st.selectbox("계산 모드", ["간편측정", "실제측정"])

    size = st.selectbox("매트 크기 선택", ["600×600", "700×700", "800×800", "1000×1000", "1200×1200"])
    material = st.selectbox("매트 재질", ["일반 TPU", "프리미엄 TPU", "패브릭 TPU"])

    material_price = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000
    }

    extend_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

    total_mats = 0

    if mode == "간편측정":
        pyeong = st.number_input("평수 입력", min_value=1)
        area_type = st.selectbox("시공 범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])

        if st.button("계산하기"):
            total_mats = simple_calc(pyeong, area_type, extend_type, size)
            st.success(f"총 매트 수량: {total_mats} 장")

    else:
        cnt = st.number_input("측정 구역 수", min_value=1)
        measures = []
        for i in range(cnt):
            w = st.number_input(f"{i+1}번 가로(mm)", min_value=1)
            h = st.number_input(f"{i+1}번 세로(mm)", min_value=1)
            measures.append((w, h))

        if st.button("계산하기"):
            total_mats = precision_calc(measures, extend_type, size)
            st.success(f"정밀 측정 수량: {total_mats} 장")

    if total_mats > 0:
        st.subheader("견적 결과")

        mat_cost = total_mats * material_price[material]
        labor_cost = int(total_mats * (int(size.split("×")[0]) / 100 * 40))
        default_final = mat_cost + labor_cost

        final_price = st.number_input("최종 견적금액 (수정 가능)", value=default_final)

        if st.button("견적서 인쇄"):
            params = (
                f"?customer={customer}"
                f"&phone={phone}"
                f"&address={address}"
                f"&date={date}"
                f"&material={material}"
                f"&size={size}"
                f"&extend={extend_type}"
                f"&mats={total_mats}"
                f"&mat_cost={mat_cost}"
                f"&labor_cost={labor_cost}"
                f"&final_cost={final_price}"
            )

            st.markdown(
                f"""
                <script>
                window.open('/print{params}', '_blank');
                </script>
                """,
                unsafe_allow_html=True
            )


# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
else:
    main()