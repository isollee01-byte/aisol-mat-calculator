import streamlit as st

st.set_page_config(page_title="견적서 인쇄", layout="wide")

# Query params 받기
q = st.query_params

customer = q.get("customer", "")
phone = q.get("phone", "")
address = q.get("address", "")
date = q.get("date", "")
material = q.get("material", "")
size = q.get("size", "")
extend_type = q.get("extend", "")
mats = q.get("mats", "")
mat_cost = q.get("mat_cost", "")
labor_cost = q.get("labor_cost", "")
final_cost = q.get("final_cost", "")

# 로고
import base64
try:
    with open("isollogo.png", "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()
except:
    LOGO_B64 = ""

# HTML 전문 견적서
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
<tr><th>고객명</th><td>{customer}</td></tr>
<tr><th>연락처</th><td>{phone}</td></tr>
<tr><th>주소</th><td>{address}</td></tr>
</table>


<div class="section-header">③ 시공 정보</div>
<table>
<tr><th>매트 재질</th><td>{material}</td></tr>
<tr><th>매트 크기</th><td>{size}</td></tr>
<tr><th>확장 여부</th><td>{extend_type}</td></tr>
<tr><th>시공 희망일</th><td>{date}</td></tr>
</table>


<div class="section-header">④ 비용 산출 내역</div>
<table>
<tr><th>총 매트 수량</th><td>{mats} 장</td></tr>
<tr><th>재료비</th><td>{int(mat_cost):,} 원</td></tr>
<tr><th>시공비</th><td>{int(labor_cost):,} 원</td></tr>
<tr><th><b>최종 견적(VAT 포함)</b></th><td><b>{int(final_cost):,} 원</b></td></tr>
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

st.markdown(html, unsafe_allow_html=True)