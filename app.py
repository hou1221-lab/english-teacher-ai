import streamlit as st
import requests
import json
import pandas as pd
import re
import random
import base64
from PIL import Image
import io

# --- 1. 核心設定 ---
API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 定義兩種可能的門牌號碼 (解決 v1/v1beta 和 models/ 的矛盾)
ENDPOINTS = [
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={API_KEY}"
]

# 試算表連結
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 工具函數 ---
def img_to_base64(image):
    buffered = io.BytesIO()
    if image.mode != 'RGB': image = image.convert('RGB')
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def load_data():
    try:
        return pd.read_csv(CSV_URL).to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()

# --- 3. 側邊欄 ---
st.sidebar.title("🧑‍🏫 雲端選單")
page = st.sidebar.radio("模式", ["📸 拍照同步題庫", "✍️ 練習模式"])

# --- 4. 拍照辨識邏輯 (全自動換門牌版) ---
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立題庫")
    uploaded_file = st.file_uploader("上傳單字照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        
        if st.button("🚀 開始辨識"):
            with st.spinner('正在尋找正確的 AI 入口...'):
                base64_data = img_to_base64(img)
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": "Read the words. Return ONLY JSON array: [{'word':'...', 'definition':'...', 'hint':'...'}]"},
                            {"inline_data": {"mime_type": "image/jpeg", "data": base64_data}}
                        ]
                    }]
                }
                
                success = False
                for url in ENDPOINTS:
                    try:
                        response = requests.post(url, json=payload)
                        res_data = response.json()
                        
                        if 'candidates' in res_data:
                            ai_text = res_data['candidates'][0]['content']['parts'][0]['text']
                            match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                            if match:
                                st.session_state.word_bank = json.loads(match.group())
                                st.success("🎉 大成功！終於連通了！")
                                st.table(st.session_state.word_bank)
                                st.balloons()
                                success = True
                                break # 成功就跳出迴圈
                    except:
                        continue # 失敗就試下一個網址
                
                if not success:
                    st.error("試了所有入口都失敗。請確認：1. API 金鑰是否過期 2. 帳號是否有免費額度。")

elif "✍️ 練習模式" in page:
    st.title("✍️ 練習模式")
    st.write(st.session_state.word_bank)
