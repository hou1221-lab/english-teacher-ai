import streamlit as st
import pandas as pd
import random

# --- 1. 設定頁面 ---
st.set_page_config(page_title="英文單字小老師", layout="centered")

# --- 2. 你的單字庫 (直接寫在這裡，不會連線失敗) ---
# 你可以在這裡隨時增加或修改單字
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = [
        {"word": "accord", "definition": "[n]一致、符合", "hint": "a"},
        {"word": "acceptable", "definition": "[a]可接受的，合意的", "hint": "a"},
        {"word": "accident", "definition": "[n]意外事件，事故", "hint": "a"},
        {"word": "account", "definition": "[n]計算, 帳目, 說明, 估計, 理由", "hint": "a"},
        {"word": "accurate", "definition": "[a]正確的, 精確的", "hint": "a"},
        {"word": "ache", "definition": "[n]疼痛 ; [vi]覺得疼痛, 渴望", "hint": "a"},
        {"word": "achieve", "definition": "[vt]完成, 達到", "hint": "a"},
        {"word": "achievement", "definition": "[n]成就, 功勳", "hint": "a"},
        {"word": "activity", "definition": "[n]活躍, 活動性, 行動, 行為", "hint": "a"},
        {"word": "actual", "definition": "[a]實際的, 真實的, 現行的, 目前的", "hint": "a"}
    ]

if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 左側選單 (第一頁、第二頁回來了) ---
st.sidebar.title("📚 學習選單")
page = st.sidebar.radio("請選擇模式", ["📸 第一頁：我的題庫", "✍️ 第二頁：拼字大挑戰"])

# --- 4. 功能頁面 ---

# 第一頁：我的題庫 (直接讀取，不用辨識)
if page == "📸 第一頁：我的題庫":
    st.title("📸 我的英文題庫")
    st.write("這是你目前的單字表：")
    
    # 直接用表格顯示單字
    df = pd.DataFrame(st.session_state.word_bank)
    st.table(df)
    
    st.info("💡 小提示：你可以直接在 app.py 程式碼中修改單字內容喔！")

# 第二頁：拼字練習
elif page == "✍️ 第二頁：拼字大挑戰":
    st.title("✍️ 拼字大挑戰")
    
    if st.button("🎯 隨機抽一題") or st.session_state.current_q is None:
        st.session_state.current_q = random.choice(st.session_state.word_bank)
        st.session_state.feedback = ""
    
    q = st.session_state.current_q
    st.subheader(f"中文意思：{q['definition']}")
    st.write(f"提示：首字母是 **{q['hint']}**，長度為 {len(q['word'])} 個字母")
    
    user_input = st.text_input("請輸入英文單字：", key="quiz_input").strip()
    
    if st.button("提交答案"):
        if user_input.lower() == q['word'].lower():
            st.success("🎉 太棒了！答對了！")
            st.balloons()
        else:
            st.error(f"再接再厲！正確答案是：{q['word']}")
