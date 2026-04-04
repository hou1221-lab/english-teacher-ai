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
    "🧠 第三頁：題庫大挑戰 (十題連發)"
])

if st.sidebar.button("🗑️ 重設所有題目"):
    st.session_state.word_bank = []
    st.rerun()

# --- 3. 家長出題區 (手動打字，最穩！) ---
if page == "🔒 家長出題區 (手動輸入)":
    st.title("🔒 家長手動出題")
    st.write("請家長在這裡輸入單字，孩子在其他頁面練習時看不見這裡。")
    
    with st.form("add_word", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            eng = st.text_input("英文單字 (如: apple)")
        with c2:
            chi = st.text_input("中文意思 (如: 蘋果)")
        
        if st.form_submit_button("➕ 加入題庫"):
            if eng and chi:
                st.session_state.word_bank.append({"word": eng.strip(), "definition": chi.strip()})
                st.success(f"已加入：{eng}")
            else:
                st.error("兩個欄位都要填喔！")

    if st.session_state.word_bank:
        st.subheader("📋 目前已建立的單字")
        st.table(pd.DataFrame(st.session_state.word_bank))

# --- 4. 第一頁：拼字練習 (10題就出10題) ---
elif page == "✍️ 第一頁：拼字練習":
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("題庫空空的，請家長先去出題喔！")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            
            # 顯示提示 a____
            hint = f"{item['word'][0]} {'_' * (len(item['word'])-1)}"
            ans = st.text_input(f"請拼出單字 (提示：{hint})", key=f"spell_{i}").strip()
            
            if ans.lower() == item['word'].lower():
                st.success("✅ 正確！")

# --- 5. 第二頁：中選英 (給中文選英文) ---
elif page == "🎮 第二頁：中選英 (四選一)":
    st.title("🎮 中文選英文")
    if len(st.session_state.word_bank) < 4:
        st.warning("單字量不足 4 個，無法產生選項。")
    else:
        # 隨機選一題
        if 'q2_idx' not in st.session_state: st.session_state.q2_idx = 0
        
        target = st.session_state.word_bank[st.session_state.q2_idx]
        st.markdown(f"<p class='big-font'>請問「{target['definition']}」的英文是？</p>", unsafe_allow_html=True)
        
        # 製作選項
        correct = target['word']
        others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
        opts = random.sample(others, min(len(others), 3)) + [correct]
        random.shuffle(opts)
        
        choice = st.radio("選擇答案：", opts, key=f"q2_radio_{st.session_state.q2_idx}")
        if st.button("檢查答案"):
            if choice == correct:
                st.success("🎉 太棒了！")
                st.balloons()
                if st.session_state.q2_idx < len(st.session_state.word_bank) - 1:
                    st.session_state.q2_idx += 1
            else:
                st.error("選錯了，再試試看！")

# --- 6. 第三頁：題庫大挑戰 (從題庫中找適合的單字) ---
elif page == "🧠 第三頁：題庫大挑戰 (十題連發)":
    st.title("🧠 題庫綜合選擇題")
    if len(st.session_state.word_bank) < 4:
        st.warning("單字量不足，請家長多加幾個單字。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>{i+1}. 哪一個單字代表「{item['definition']}」？</p>", unsafe_allow_html=True)
            
            correct = item['word']
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
            opts = random.sample(others, min(len(others), 3)) + [correct]
            random.shuffle(opts)
            
            choice = st.selectbox("請選擇：", ["請選擇..."] + opts, key=
