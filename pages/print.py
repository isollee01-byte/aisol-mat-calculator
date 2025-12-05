import streamlit as st
import base64

st.set_page_config(page_title="견적서 인쇄", layout="wide")

# ------------------------------
# 쿼리 파라미터 수신
# ------------------------------
params = st.experimental_get_query_params()

def get_param(key, default=""):
    val = params.get(key, [default])
    return val[0] if isinstance(val, list) else val

customer   = get_param("customer")
phone      = get_param("phone")
address    = get_param("address")
date       = get_param("date")
material   = get_param("material")
size       = get_param("size")
extend     = get_param("extend")
mats       = get_param("mats", "0")
mat_cost   = int(get_param("mat_cost", "0") or 0)
labor_cost = int(get_param("labor_cost", "0") or 0)
final_cost = int(get_param("final_cost", "0") or 0)

# ------------------------------
# 로고 Base64
# ------------------------------
def load_logo_base64():
    try:
        with open("isollogo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

LOGO_B64 = load_logo_base64()

# ------------------------------
# A4 견적서 HTML
# ------------------------------
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
<tr><th>계산 방식</th><td>{extend}</td></tr>
<tr><th>시공 희망일</th><td>{date}</td></tr>
</table>


<div class="section-header">④ 비용 산출 내역</div>
<table>
<tr><th>총 매트 수량</th><td>{mats} 장</td></tr>
<tr><th>재료비</th><td>{mat_cost:,} 원</td></tr>
<tr><th>시공비</th><td>{labor_cost:,} 원</td></tr>
<tr><th><b>최종 견적(VAT 포함)</b></th><td><b>{final_cost:,} 원</b></td></tr>
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