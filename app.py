import streamlit as st
import requests
import json
import pandas as pd
import re
import random
import base64
from PIL import Image
import io

# --- 1. 核心安全設定 ---
# 使用你最新的 API Key
API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 自動切換多個備用入口，確保絕對連得上 Google
ENDPOINTS = [
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={API_KEY}"
]

st.set_page_config(page_title="英文單字 AI 小老師", layout="centered", page_icon="📝")

# --- 2. 工具函數 ---
def img_to_base64(image):
    buffered = io.BytesIO()
    if image.mode != 'RGB': image = image.convert('RGB')
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# 初始化網頁內部的單字庫（不依賴試算表）
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = []
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 側邊欄選單 ---
st.sidebar.title("🎮 學習選單")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步單字", "✍️ 拼字大挑戰"])

if st.sidebar.button("🗑️ 清空所有單字"):
    st.session_state.word_bank = []
    st.session_state.current_q = None
    st.rerun()

# --- 4. 模式邏輯 ---

# 模式一：拍照同步
if page == "📸 拍照同步單字":
    st.title("📸 拍照同步單字")
    st.write("上傳課本或講義的照片，AI 會自動幫你整理成題庫！")
    
    uploaded_file = st.file_uploader("選擇照片...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="已上傳的照片", use_container_width=True)
        
        if st.button("🚀 讓 AI 開始辨識"):
            with st.spinner('AI 老師正在讀取單字中...'):
                base64_data = img_to_base64(img)
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Extract English words and Chinese meanings from this image. Return ONLY a JSON array of objects: [{'word':'...', 'definition':'...', 'hint':'...'}]"},
                            {"inline_data": {"mime_type": "image/jpeg", "data": base64_data}}
                        ]
                    }]
                }
                
                success = False
                for url in ENDPOINTS:
                    try:
                        response = requests.post(url, json=payload, timeout=10)
                        res_data = response.json()
                        
                        if 'candidates' in res_data:
                            ai_text = res_data['candidates'][0]['content']['parts'][0]['text']
                            # 提取 JSON 部分
                            match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                            if match:
                                new_words = json.loads(match.group())
                                st.session_state.word_bank = new_words
                                st.success(f"✅ 成功辨識出 {len(new_words)} 個單字！")
                                st.table(pd.DataFrame(new_words))
                                st.balloons()
                                success = True
                                break
                    except:
                        continue
                
                if not success:
                    st.error("❌ 連線失敗。請確認網路狀況，或重新整理頁面。")

# 模式二：拼字挑戰
elif page == "✍️ 拼字大挑戰":
    st.title("✍️ 拼字大挑戰")
    
    if not st.session_state.word_bank:
        st.warning("⚠️ 目前沒有單字，請先去拍照喔！")
    else:
        if st.button("🎯 隨機抽一題") or st.session_state.current_q is None:
            st.session_state.current_q = random.choice(st.session_state.word_bank)
            st.session_state.feedback = ""
        
        q = st.session_state.current_q
        st.subheader(f"中文意思：{q['definition']}")
        st.write(f"提示：字首為 **{q['hint']}**，長度為 {len(q['word'])} 個字母")
        
        user_input = st.text_input("請輸入英文單字：", key="quiz_input").strip()
        
        if st.button("提交答案"):
            if user_input.lower() == q['word'].lower():
                st.success("🎉 太棒了！答對了！")
                st.balloons()
            else:
                st.error
