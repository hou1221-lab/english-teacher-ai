import streamlit as st
import pandas as pd
import random
import re
from PIL import Image

# =========================================
# 1. 基本設定與 CSS (字體放大)
# =========================================
st.set_page_config(page_title="孩子英文學習機", layout="centered", page_icon="📝")

st.markdown("""
<style>
/* 放大輸入框字體 */
.stTextInput input {
    font-size: 30px !important;
    height: 60px !important;
    font-weight: bold !important;
}
/* 放大題目字體 */
.big-font {
    font-size: 30px !important;
    font-weight: bold !important;
    line-height: 1.6;
}
/* 放大選擇題選項字體 */
div[data-baseweb="radio"] label {
    font-size: 24px !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

# 初始化題庫
if "word_bank" not in st.session_state:
    st.session_state.word_bank = []

# =========================================
# 2. 工具函式
# =========================================
def get_hint(word):
    if len(word) <= 1: return word
    return word[0] + " " + " ".join(["_"] * (len(word) - 1))

# =========================================
# 3. 側邊欄導覽
# =========================================
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio(
    "切換頁面",
    ["📷 家長上傳區", "✍️ 第一頁：拼字練習", "🎯 第二頁：中選英 (四選一)", "🧠 第三頁：題庫總複習"]
)

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    st.rerun()

# =========================================
# 4. 家長上傳區 (支援手動輸入)
# =========================================
if page == "📷 家長上傳區":
    st.title("📷 家長出題區")
    
    with st.form("add_word", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: eng = st.text_input("英文單字").strip().lower()
        with c2: chi = st.text_input("中文意思").strip()
        if st.form_submit_button("➕ 加入題庫"):
            if eng and chi:
                st.session_state.word_bank.append({"word": eng, "definition": chi})
                st.success(f"已加入：{eng}")

    if st.session_state.word_bank:
        st.subheader("📋 目前題庫清單")
        st.table(pd.DataFrame(st.session_state.word_bank))

# =========================================
# 5. 第一頁：中文提示拼英文 (字體放大)
# =========================================
elif page == "✍️ 第一頁：拼字練習":
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("請先建立題庫。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            hint = get_hint(item["word"])
            ans = st.text_input(f"提示：{hint}", key=f"spell_{i}").strip().lower()
            if ans == item["word"]:
                st.success("✅ 正確")

# =========================================
# 6. 第二頁：中選英 (考中文意思，選英文單字)
# =========================================
elif page == "🎯 第二頁：中選英 (四選一)":
    st.title("🎯 中文選英文")
    if len(st.session_state.word_bank) < 4:
        st.warning("至少需要 4 個單字。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            
            # 生成選項
            correct = item['word']
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
            choices = random.sample(others, min(3, len(others))) + [correct]
            random.shuffle(choices)
            
            user_choice = st.radio(f"請選出正確的單字：", choices, key=f"mc_{i}")
            if st.button("檢查答案", key=f"btn_{i}"):
                if user_choice == correct: st.success("🎉 答對了")
                else: st.error(f"不對喔，正確答案是：{correct}")

# =========================================
# 7. 第三頁：題庫總複習 (10個單字就出10題)
# =========================================
elif page == "🧠 第三頁：題庫總複習":
    st.title("🧠 題庫綜合挑戰")
    if len(st.session_state.word_bank) < 4:
        st.warning("至少需要 4 個單字。")
    else:
        score = 0
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>{i+1}. 哪一個單字是「{item['definition']}」？</p>", unsafe_allow_html=True)
            
            correct = item['word']
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
            choices = random.sample(others, min(3, len(others))) + [correct]
            random.shuffle(choices)
            
            user_choice = st.radio(f"選擇答案：", choices, key=f"final_{i}")
            if user_choice == correct: score += 1

        if st.button("📊 送出結算分數"):
            st.success(f"最終得分：{score} / {len(st.session_state.word_bank)}")
            if score == len(st.session_state.word_bank):
                st.balloons()
