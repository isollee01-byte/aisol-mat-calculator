import math
import streamlit as st

# 변환 상수
PYEONG_TO_M2 = 3.3058
MAT_AREA = 0.64  # 800×800mm 매트 1장 = 0.64m²

def calc(pyeong, is_expanded):
    areas = {
        "거실": pyeong * 0.93 * PYEONG_TO_M2,
        "거실+복도": pyeong * 1.46 * PYEONG_TO_M2,
        "거실+복도+아이방1": pyeong * 1.67 * PYEONG_TO_M2,
        "거실+복도+주방": pyeong * 2.00 * PYEONG_TO_M2,
    }

    results = {}

    for name, area in areas.items():
        base = math.ceil(area / MAT_AREA)
        adj = base if is_expanded else max(base - 8, 0)
        final = math.ceil(adj * 1.10)

        results[name] = {
            "면적(m²)": round(area, 2),
            "기본 필요 장수": base,
            "보정 장수(확장/비확장)": adj,
            "최종 권장 장수(+10%)": final
        }
    return results


st.title("🧮 아이솔 800×800 매트 자동 계산기")

pyeong = st.number_input("전용면적(평)을 입력하세요:", min_value=1.0, step=0.5)
expand_choice = st.radio("확장형 여부:", ["확장형", "비확장형"])
is_expanded = (expand_choice == "확장형")

if st.button("계산하기"):
    outcome = calc(pyeong, is_expanded)
    
    st.subheader("📌 계산 결과")
    for section, values in outcome.items():
        st.write(f"### ▶ {section}")
        st.json(values)
