import streamlit as st
import pandas as pd
import random

# --- 1. 基礎設定 ---
st.set_page_config(page_title="孩子英文學習機", layout="centered", page_icon="📝")

# 強制放大輸入框文字與題目文字
st.markdown("""
    <style>
    .stTextInput input {
        font-size: 30px !important;
        height: 60px !important;
        font-weight: bold !important;
    }
    .big-font {
        font-size: 32px !important;
        font-weight: bold !important;
        line-height: 1.5;
    }
    /* 放大單選按鈕的字體 */
    div[data-baseweb="radio"] label {
        font-size: 24px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化單字庫 (存在網頁記憶體)
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = []

# --- 2. 左側選單 ---
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio("切換頁面", [
    "🔒 家長出題區 (手動輸入)", 
    "✍️ 第一頁：拼字練習", 
    "🎮 第二頁：中選英 (四選一)",
    "🧠 第三頁：題庫大挑戰"
])

if st.sidebar.button("🗑️ 重設所有題目"):
    st.session_state.word_bank = []
    st.rerun()

# --- 3. 家長出題區 ---
if page == "🔒 家長出題區 (手動輸入)":
    st.title("🔒 家長手動出題")
    st.write("請在這裡輸入單字。")
    
    with st.form("add_word", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            eng = st.text_input("英文單字")
        with c2:
            chi = st.text_input("中文意思")
        
        if st.form_submit_button("➕ 加入題庫"):
            if eng and chi:
                st.session_state.word_bank.append({"word": eng.strip(), "definition": chi.strip()})
                st.success(f"已加入：{eng}")
            else:
                st.error("欄位不能空白喔！")

    if st.session_state.word_bank:
        st.subheader("📋 目前已建立的單字表")
        st.table(pd.DataFrame(st.session_state.word_bank))

# --- 4. 第一頁：拼字練習 ---
elif page == "✍️ 第一頁：拼字練習":
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("請家長先去出題區輸入單字喔！")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            hint = f"{item['word'][0]} {'_' * (len(item['word'])-1)}"
            ans = st.text_input(f"請拼出單字 (提示：{hint})", key=f"spell_{i}").strip()
            if ans.lower() == item['word'].lower():
                st.success("✅ 正確！")

# --- 5. 第二頁：中選英 (四選一) ---
elif page == "🎮 第二頁：中選英 (四選一)":
    st.title("🎮 中文選英文")
    if len(st.session_state.word_bank) < 4:
        st.warning("單字量至少要 4 個才能玩選擇題喔！")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：請問「{item['definition']}」的英文是？</p>", unsafe_allow_html=True)
            
            correct = item['word']
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
            opts = random.sample(others, min(len(others), 3)) + [correct]
            random.shuffle(opts)
            
            choice = st.radio("選擇答案：", opts, key=f"q2_{i}")
            if st.button("檢查答案", key=f"btn2_{i}"):
