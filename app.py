import streamlit as st
import pandas as pd
import random

# --- 1. 基礎設定 ---
st.set_page_config(page_title="孩子英文學習機", layout="centered", page_icon="🍎")

# 初始化單字庫 (存在網頁記憶體中)
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = []

# --- 2. 左側導覽選單 ---
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio("請選擇頁面", ["📝 第一頁：家長建立單字", "🎮 第二頁：英語選擇題"])

if st.sidebar.button("🗑️ 重設所有單字"):
    st.session_state.word_bank = []
    st.rerun()

# --- 3. 第一頁：家長手動建立單字 ---
if page == "📝 第一頁：家長建立單字":
    st.title("📝 建立今日單字")
    st.write("請在下方輸入想讓孩子練習的單字與中文。")
    
    # 建立輸入區
    with st.form("word_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_word = st.text_input("英文單字 (例如: apple)").strip()
        with col2:
            new_def = st.text_input("中文意思 (例如: 蘋果)").strip()
        
        submitted = st.form_submit_button("➕ 加入題庫")
        if submitted and new_word and new_def:
            # 自動抓取首字母作為提示
            hint = new_word[0].lower() if len(new_word) > 0 else ""
            st.session_state.word_bank.append({
                "word": new_word,
                "definition": new_def,
                "hint": hint
            })
            st.success(f"已加入：{new_word} ({new_def})")

    # 顯示目前已有的單字
    if st.session_state.word_bank:
        st.subheader("👀 目前的單字清單")
        df = pd.DataFrame(st.session_state.word_bank)
        st.table(df)
        
        # 拼字練習區
        st.divider()
        st.subheader("✍️ 孩子拼字練習")
        target = st.session_state.word_bank[-1] # 以最後加入的單字練習
        st.write(f"題目：**{target['definition']}**")
        st.write(f"提示：{target['word'][0]} {' _ ' * (len(target['word'])-1)}")
        
        child_ans = st.text_input("孩子請在這裡打上單字：", key="child_spell")
        if child_ans:
            if child_ans.lower() == target['word'].lower():
                st.success("🎉 太棒了！拼對了！")
                st.balloons()
            else:
                st.info("加油！再試一次喔！")

# --- 4. 第二頁：英語選擇題模式 ---
elif page == "🎮 第二頁：英語選擇題":
    st.title("🎮 英語選擇題挑戰")
    
    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 題庫至少需要 4 個單字才能玩選擇題喔！請先回第一頁增加單字。")
    else:
        if st.button("🎲 產生新題目") or 'quiz_q' not in st.session_state:
            # 隨機選一個正確答案
            correct_item = random.choice(st.session_state.word_bank)
            # 隨機選三個錯誤答案
            others = [w['definition'] for w in st.session_state.word_bank if w != correct_item]
            wrong_choices = random.sample(others, 3)
            
            choices = wrong_choices + [correct_item['definition']]
            random.shuffle(choices) # 打亂選項順序
            
            st.session_state.quiz_q = correct_item['word']
            st.session_state.quiz_ans = correct_item['definition']
            st.session_state.quiz_choices = choices

        st.subheader(f"請問單字 **{st.session_state.quiz_q}** 是什麼意思？")
        
        # 使用按鈕或下拉選單讓孩子選
        user_choice = st.radio("請選擇最正確的答案：", st.session_state.quiz_choices)
        
        if st.button("確認答案"):
            if user_choice == st.session_state.quiz_ans:
                st.success(f"✅ 沒錯！{st.session_state.quiz_q} 就是 {st.session_state.quiz_ans}！")
                st.balloons()
            else:
                st.error("❌ 選錯了，再觀察看看喔！")
