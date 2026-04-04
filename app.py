import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re
import random
import pandas as pd

# --- 1. 核心安全設定 ---
# 這裡請確保您已在 Streamlit 的 Secrets 設定好 GEMINI_API_KEY
API_KEY = st.secrets.get("GEMINI_API_KEY") or "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 配置 Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="孩子英文學習機", layout="centered", page_icon="📝")

# --- 🎯 CSS 樣式：字體放大 🎯 ---
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
    div[data-baseweb="radio"] label {
        font-size: 24px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化題庫
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = []

# --- 2. 側邊欄選單 ---
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio("切換頁面", [
    "📷 家長上傳區 (照片辨識)", 
    "✍️ 第一頁：拼字練習 (字體大)", 
    "🎯 第二頁：中選英 (四選一)",
    "🧠 第三頁：題庫總複習 (十題連發)"
])

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    st.rerun()

# --- 3. 家長上傳區 (核心改動：加入照片辨識) ---
if page == "📷 家長上傳區 (照片辨識)":
    st.title("📷 家長拍照出題")
    st.write("請上傳單字照片，AI 會自動幫您讀取單字（照片會自動隱藏，孩子看不見）。")
    
    uploaded_file = st.file_uploader("選擇單字照片", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        # 不在這裡 st.image(img)，確保隱私
        
        if st.button("🚀 開始辨識並建立題庫"):
            with st.spinner('AI 老師正在讀取單字中...'):
                try:
                    # 傳送指令給 AI 辨識圖片內容
                    prompt = "Extract English words and their Chinese definitions from this image. Return ONLY a JSON list: [{'word':'英文','definition':'中文'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 用正則表達式抓取 JSON 內容
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        new_words = json.loads(match.group())
                        st.session_state.word_bank = new_words
                        st.success(f"✅ 成功辨識出 {len(new_words)} 個單字！單字已儲存。")
                        st.balloons()
                    else:
                        st.error("AI 沒看清楚圖片內容，請換一張更清晰的照片試試。")
                except Exception as e:
                    st.error(f"連線出錯：{str(e)}")
                    st.info("請確認您的 API Key 是否有效。")

    # 顯示目前題庫 (給家長確認)
    if st.session_state.word_bank:
        st.subheader("📋 目前題庫清單")
        st.table(pd.DataFrame(st.session_state.word_bank))

# --- 4. 第一頁：拼字練習 (10題連發) ---
elif page == "✍️ 第一頁：拼字練習 (字體大)":
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("⚠️ 題庫空空的，請家長先上傳照片喔！")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            # 提示：第一個字 + 底線
            hint = f"{item['word'][0].upper()} {'_ ' * (len(item['word'])-1)}"
            ans = st.text_input(f"提示：{hint}", key=f"spell_{i}").strip().lower()
            if ans == item['word'].lower():
                st.success("✨ 正確！")

# --- 5. 第二頁：中選英 (四選一) ---
elif page == "🎯 第二頁：中選英 (四選一)":
    st.title("🎯 中文選英文")
    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 至少要辨識 4 個單字才能玩選擇題喔！")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            
            # 隨機產生選項
            correct = item['word']
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
            opts = random.sample(others, min(3, len(others))) + [correct]
            random.shuffle(opts)
            
            user_choice = st.radio(f"請選出單字：", opts, key=f"q2_{i}")
            if st.button("檢查答案", key=f"btn2_{i}"):
                if user_choice == correct: st.success("🎉 太棒了！")
                else: st.error(f"不對喔，正確答案是：{correct}")

# --- 6. 第三頁：題庫總複習 ---
elif page == "🧠 第三頁：題庫總複習 (十題連發)":
    st.title("🧠 題庫總複習")
    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 題庫單字不足。")
    else:
        score = 0
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"<p class='big-font'>{i+1}. 「{item['definition']}」是哪個單字？</p>", unsafe_allow_html=True)
            
            correct = item['word']
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct]
            opts = random.sample(others, min(3, len(others))) + [correct]
            random.shuffle(opts)
            
            user_choice = st.radio(f"請選擇：", opts, key=f"q3_{i}")
            if user_choice == correct: score += 1
        
        if st.button("📊 送出結算分數"):
            st.success(f"總分：{score} / {len(st.session_state.word_bank)}")
            if score == len(st.session_state.word_bank):
                st.balloons()
