import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re
import random

# --- 1. 核心設定 ---
API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="英文學習小老師", layout="centered")

# 初始化資料庫
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = []

# --- 2. 側邊欄選單 ---
st.sidebar.title("🍀 學習選單")
page = st.sidebar.radio("切換頁面", [
    "🔒 家長拍照區", 
    "✍️ 第一頁：拼字填空題", 
    "📋 第二頁：單字總複習",
    "🧠 第三頁：情境選擇題"
])

# --- 3. 家長拍照區（隱藏圖片） ---
if page == "🔒 家長拍照區":
    st.title("🔒 家長出題區")
    st.write("請家長拍照或上傳單字表，辨識完成後請切換頁面給孩子練習。")
    
    uploaded_file = st.file_uploader("上傳單字照片", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        if st.button("🚀 開始辨識並隱藏圖片"):
            img = Image.open(uploaded_file)
            with st.spinner('AI 正在讀取單字中...'):
                try:
                    prompt = "Read image. Return ONLY a JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        st.session_state.word_bank = json.loads(match.group())
                        st.success(f"✅ 成功辨識 {len(st.session_state.word_bank)} 個單字！圖片已自動遮蔽。")
                        st.balloons()
                    else:
                        st.error("辨識失敗，請換張照片。")
                except Exception as e:
                    st.error(f"連線錯誤：{e}")

# --- 4. 第一頁：拼字填空題 (10個單字=10題) ---
elif page == "✍️ 第一頁：拼字填空題":
    st.title("✍️ 拼字填空挑戰")
    if not st.session_state.word_bank:
        st.warning("請家長先去拍照出題喔！")
    else:
        st.write("請看中文意思，打出正確的英文單字：")
        correct_count = 0
        for i, item in enumerate(st.session_state.word_bank):
            st.subheader(f"第 {i+1} 題：{item['definition']}")
            # 顯示提示如 a _ _ _ _
            placeholder = f"{item['word'][0].upper()} {'_ ' * (len(item['word'])-1)}"
            ans = st.text_input(f"提示：{placeholder}", key=f"spell_{i}").strip()
            if ans.lower() == item['word'].lower():
                st.success("正確！✨")
                correct_count += 1
        
        if correct_count == len(st.session_state.word_bank):
            st.balloons()

# --- 5. 第二頁：單字總複習 ---
elif page == "📋 第二頁：單字總複習":
    st.title("📋 今日單字清單")
    if not st.session_state.word_bank:
        st.warning("目前沒有單字。")
    else:
        st.table(st.session_state.word_bank)

# --- 6. 第三頁：情境選擇題 ---
elif page == "🧠 第三頁：情境選擇題":
    st.title("🧠 情境測驗 (例句選擇)")
    if len(st.session_state.word_bank) < 2:
        st.warning("單字量不足，無法生成選擇題。")
    else:
        # 隨機選一題
        if 'quiz_idx' not in st.session_state or st.button("換一題挑戰"):
            st.session_state.quiz_idx = random.randint(0, len(st.session_state.word_bank)-1)
            
            # 叫 AI 生一個例句
            target_word = st.session_state.word_bank[st.session_state.quiz_idx]['word']
            try:
                gen_prompt = f"Write a simple English sentence using the word '{target_word}'. Replace '{target_word}' with '_____' in the sentence."
                res = model.generate_content(gen_prompt)
                st.session_state.quiz_sentence = res.text
            except:
                st.session_state.quiz_sentence = f"An _____ a day keeps the doctor away." # 備用

        st.subheader("請根據句子意思選出正確單字：")
        st.info(st.session_state.quiz_sentence)
        
        # 製作選項
        correct_ans = st.session_state.word_bank[st.session_state.quiz_idx]['word']
        others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct_ans]
        options = random.sample(others, min(len(others), 3)) + [correct_ans]
        random.shuffle(options)
        
        user_choice = st.radio("你的選擇：", options)
        if st.button("檢查答案"):
            if user_choice == correct_ans:
                st.success("太厲害了！完全正確！")
                st.balloons()
            else:
                st.error("再想一下喔，這題有點難！")
