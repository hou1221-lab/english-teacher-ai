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
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

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

# --- 4. 拍照辨識邏輯 (加強解析版) ---
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立題庫")
    uploaded_file = st.file_uploader("上傳單字照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        
        if st.button("🚀 開始辨識"):
            with st.spinner('AI 正在拆信中...'):
                try:
                    base64_data = img_to_base64(img)
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "Extract English-Chinese vocabulary as JSON array: [{'word':'...', 'definition':'...', 'hint':'...'}]"},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base64_data}}
                            ]
                        }]
                    }
                    
                    response = requests.post(API_URL, json=payload)
                    res_data = response.json()
                    
                    # 🛡️ 加強型解析：防止 candidates 找不到
                    if 'candidates' in res_data and len(res_data['candidates']) > 0:
                        content = res_data['candidates'][0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            ai_text = parts[0].get('text', '')
                            match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                            if match:
                                st.session_state.word_bank = json.loads(match.group())
                                st.success("🎉 大成功！單字已飛進雲端。")
                                st.table(st.session_state.word_bank)
                                st.balloons()
                            else:
                                st.error("AI 讀取成功但格式不對。")
                        else:
                            st.error("AI 沒回傳文字，請換張照片。")
                    else:
                        # 顯示更精確的錯誤，如果是額度問題就會顯示在這裡
                        err_msg = res_data.get('error', {}).get('message', 'AI 目前無法回應')
                        st.error(f"AI 老師沒開門：{err_msg}")
                        
                except Exception as e:
                    st.error(f"程式解析出錯：{e}")

elif "✍️ 練習模式" in page:
    st.title("✍️ 練習模式")
    st.write(st.session_state.word_bank)
