import streamlit as st
import math
import base64
from datetime import datetime

# --------------------------------------------------------
# 기본 페이지 설정
# --------------------------------------------------------
st.set_page_config(page_title="매트 견적 시스템", layout="centered")

# --------------------------------------------------------
# 로고 파일 → Base64 변환
# --------------------------------------------------------
def load_logo_base64():
    try:
        with open("isollogo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

LOGO_B64 = load_logo_base64()


# --------------------------------------------------------
# 로그인 화면
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
# 매트 면적 계산 함수 (m²)
# --------------------------------------------------------
def mat_area(size_str):
    w, h = size_str.split("×")
    return (int(w)/1000) * (int(h)/1000)


# --------------------------------------------------------
# 비확장형 감산 계산
# --------------------------------------------------------
def non_expand_deduction(size_str):
    lost_area = 0.64 * 8   # 800×800 기준 8장 = 5.12㎡
    area_per_mat = mat_area(size_str)
    deduction = lost_area / area_per_mat
    return max(int(round(deduction)), 0)


# --------------------------------------------------------
# 간편측정 계산
# --------------------------------------------------------
def simple_calc(pyeong, area_type, extend_type, size_str):
    factors = {
        "거실": 0.93,
        "거실+복도": 1.46,
        "거실+복도+아이방1": 1.67,
        "거실+복도+주방": 2.0
    }

    mats = pyeong * factors[area_type]

    # 올림/버림 규칙
    if mats - int(mats) <= 0.3:
        mats = int(mats)
    elif mats - int(mats) >= 0.6:
        mats = int(mats) + 1
    else:
        mats = math.ceil(mats)

    # +10% 넉넉히
    mats = int(mats * 1.10)

    # 비확장형 감산
    if extend_type == "비확장형":
        mats -= non_expand_deduction(size_str)

    return max(mats, 0)


# --------------------------------------------------------
# 실제측정 계산
# --------------------------------------------------------
def precision_calc(measures, extend_type, size_str):
    total = 0

    for w, h in measures:
        row = w / int(size_str.split("×")[0])
        col = h / int(size_str.split("×")[1])

        row = math.ceil(row)
        col = math.ceil(col)

        total += row * col

    if extend_type == "비확장형":
        total -= non_expand_deduction(size_str)

    return max(total, 0)


# --------------------------------------------------------
# 전문 견적서 HTML 생성
# --------------------------------------------------------
def build_estimate_html(data):

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>시공 견적서</title>

<style>
body {{
    font-family: 'Noto Sans KR', sans-serif;
    margin: 40px;
    color: #222;
}}

h1 {{
    text-align: center;
    font-size: 30px;
    font-weight: bold;
    margin-bottom: 35px;
}}

.section-header {{
    background: #f2f2f2;
    padding: 10px 15px;
    font-size: 19px;
    font-weight: bold;
    border-left: 5px solid #4A90E2;
    margin-top: 40px;
    margin-bottom: 10px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
    font-size: 15px;
}}

th {{
    background: #fafafa;
    width: 180px;
    border: 1px solid #444;
    padding: 10px;
    text-align: left;
}}

td {{
    border: 1px solid #444;
    padding: 10px;
}}


.watermark {{
    position: fixed;
    bottom: 40px;
    right: 40px;
    opacity: 0.08;
}}
</style>

</head>
<body>

<div style="text-align:center;">
    <img src="data:image/png;base64,{LOGO_B64}" width="120">
</div>

<h1>매트 시공 견적서</h1>

<div class="section-header">① 공급자 정보</div>
<table>
<tr><th>업체명</th><td>&nbsp;</td></tr>
<tr><th>대표자</th><td>&nbsp;</td></tr>
<tr><th>사업자등록번호</th><td>&nbsp;</td></tr>
<tr><th>주소</th><td>&nbsp;</td></tr>
<tr><th>연락처</th><td>&nbsp;</td></tr>
<tr><th>이메일</th><td>&nbsp;</td></tr>
</table>


<div class="section-header">② 소비자 정보</div>
<table>
<tr><th>고객명</th><td>{data['customer']}</td></tr>
<tr><th>연락처</th><td>{data['phone']}</td></tr>
<tr><th>주소</th><td>{data['address']}</td></tr>
</table>


<div class="section-header">③ 시공 정보</div>
<table>
<tr><th>매트 재질</th><td>{data['material']}</td></tr>
<tr><th>매트 크기</th><td>{data['size']}</td></tr>
<tr><th>확장 여부</th><td>{data['extend']}</td></tr>
<tr><th>시공 희망일</th><td>{data['date']}</td></tr>
</table>


<div class="section-header">④ 비용 산출 내역</div>
<table>
<tr><th>총 매트 수량</th><td>{data['mats']} 장</td></tr>
<tr><th>재료비</th><td>{data['material_cost']:,} 원</td></tr>
<tr><th>시공비</th><td>{data['labor_cost']:,} 원</td></tr>
<tr><th><b>최종 견적(VAT 포함)</b></th><td><b>{data['final_cost']:,} 원</b></td></tr>
</table>


<div class="section-header">⑤ 확인</div>
<table>
<tr><th>공급자 확인</th><td>&nbsp;</td></tr>
<tr><th>소비자 확인</th><td>&nbsp;</td></tr>
</table>

<img class="watermark" src="data:image/png;base64,{LOGO_B64}" width="250">

<script>
window.onload = function() {{
    window.print();
}};
</script>

</body>
</html>
"""
    return html


# --------------------------------------------------------
# 새 탭에서 견적서 출력
# --------------------------------------------------------
def open_print_window(html):
    b64 = base64.b64encode(html.encode()).decode()
    js = f"""
    <script>
        var win = window.open();
        win.document.write(atob("{b64}"));
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


# --------------------------------------------------------
# 메인 견적 계산 페이지
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

    material_unit_price = {
        "일반 TPU": 39000,
        "프리미엄 TPU": 42000,
        "패브릭 TPU": 50000
    }

    extend_type = st.selectbox("확장 여부", ["확장형", "비확장형"])

    total_mats = 0

    if mode == "간편측정":
        p = st.number_input("평수 입력", min_value=1, step=1)
        area_type = st.selectbox("시공 범위", ["거실", "거실+복도", "거실+복도+아이방1", "거실+복도+주방"])
        if st.button("계산하기"):
            total_mats = simple_calc(p, area_type, extend_type, size)
            st.success(f"총 매트 수량: {total_mats} 장")

    else:
        cnt = st.number_input("측정 구역 수", min_value=1, step=1)
        measures = []
        for i in range(cnt):
            w = st.number_input(f"{i+1}번 가로(mm)", min_value=1)
            h = st.number_input(f"{i+1}번 세로(mm)", min_value=1)
            measures.append((w, h))
        if st.button("계산하기"):
            total_mats = precision_calc(measures, extend_type, size)
            st.success(f"정밀 계산 수량: {total_mats} 장")

    if total_mats > 0:
        st.subheader("견적 결과")

        material_cost = total_mats * material_unit_price[material]
        labor_cost = int(total_mats * (int(size.split("×")[0]) / 100 * 40))  # (앞숫자 × 40) 규칙 적용
        final_default = material_cost + labor_cost

        final_cost = st.number_input("최종 견적금액(수정 가능)", value=final_default)

        if st.button("견적서 인쇄"):
            data = {
                "customer": customer,
                "phone": phone,
                "address": address,
                "date": date,
                "material": material,
                "size": size,
                "extend": extend_type,
                "mats": total_mats,
                "material_cost": material_cost,
                "labor_cost": labor_cost,
                "final_cost": final_cost
            }
            html = build_estimate_html(data)
            open_print_window(html)


# --------------------------------------------------------
# 실행
# --------------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
else:
    main()