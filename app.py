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
# 使用你最新的 API Key
API_KEY = "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 直接指定 Google 正式版的 API 網址 (避開 v1beta 標籤)
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# 試算表連結
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 工具函數 ---
def img_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def load_data():
    try:
        return pd.read_csv(CSV_URL).to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 側邊欄 ---
st.sidebar.title("🧑‍🏫 雲端選單")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

# --- 4. 模式切換 ---
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立題庫")
    st.info("🤖 目前連線：官方標準穩定通道 (REST)")
    
    uploaded_file = st.file_uploader("上傳單字照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        
        if st.button("🚀 開始辨識"):
            with st.spinner('正在與雲端伺服器對接...'):
                try:
                    # 準備圖片資料
                    base64_img = img_to_base64(img)
                    
                    # 準備傳送給 Google 的信件內容 (JSON)
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": "List English words and Chinese meanings from image as JSON list: [{'word':'...', 'definition':'...', 'hint':'...'}]"},
                                {"inline_data": {"mime_type": "image/jpeg", "data": base64_img}}
                            ]
                        }]
                    }
                    
                    # 直接「寄信」給 Google
                    response = requests.post(API_URL, json=payload)
                    res_json = response.json()
                    
                    # 解析回傳內容
                    ai_text = res_json['candidates'][0]['content']['parts'][0]['text']
                    match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                    
                    if match:
                        st.session_state.word_bank = json.loads(match.group())
                        st.success(f"✅ 成功辨識 {len(st.session_state.word_bank)} 個單字！")
                        st.table(st.session_state.word_bank)
                        st.balloons()
                    else:
                        st.error("AI 讀取成功，但找不到單字列表。")
                except Exception as e:
                    st.error(f"連線還是失敗嗎？錯誤：{e}")
                    st.warning("如果持續出現錯誤，請確認 API Key 是否在 Google AI Studio 仍顯示為有效。")

elif "✍️ Lv1. 拼字大挑戰" in page:
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("題庫空空的，請先拍照喔！")
    else:
        if st.button("🎯 換一題") or st.session_state.current_q is None:
            st.session_state.current_q = random.choice(st.session_state.word_bank)
        q = st.session_state.current_q
        st.subheader(f"中文意思：{q['definition']}")
        ans = st.text_input("請輸入單字：").strip()
        if st.button("檢查答案"):
            if ans.lower() == q['word'].lower():
                st.success("🎉 答對了！")
                st.balloons()
            else:
                st.error(f"差一點！正確答案是：{q['word']}")

elif "🧠 Lv2. 小六情境測驗" in page:
    st.title("🧠 情境測驗")
    st.write("雲端同步正常。")
