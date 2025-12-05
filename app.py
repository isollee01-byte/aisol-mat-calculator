import math
import streamlit as st

# ----------------------------
# 계산 함수 (평수 × 계수 방식)
# ----------------------------
def calculate_mats(pyeong, is_expanded):

    # 평수 기반 장수 계산 공식
    base_values = {
        "거실": pyeong * 0.93,
        "거실+복도": pyeong * 1.46,
        "거실+복도+아이방1": pyeong * 1.67,
        "거실+복도+주방": pyeong * 2.00,
    }

    results = {}

    for name, value in base_values.items():
        base = math.ceil(value)                        # 기본 장수 (평수 × 계수)
        adj = base if is_expanded else max(base - 8, 0)  # 비확장형이면 -8장
        final = math.ceil(adj * 1.10)                   # +10% 여유분 적용

        results[name] = {
            "기본 장수(평×계수)": base,
            "보정 장수(확장/비확장)": adj,
            "최종 권장 장수(+10%)": final
        }

    return results


# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🧮 아이솔 800×800 매트 자동 계산기 (평수 기반)")

pyeong = st.number_input("전용면적(평)을 입력하세요:", min_value=1.0, step=0.5)

expand_choice = st.radio("확장형 여부:", ["확장형", "비확장형"])
is_expanded = (expand_choice == "확장형")

if st.button("계산하기"):
    output = calculate_mats(pyeong, is_expanded)

    st.subheader("📌 계산 결과")
    for section, values in output.items():
        st.write(f"### ▶ {section}")
        st.json(values)
