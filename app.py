import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re

# --- 1. 核心設定 ---
genai.configure(api_key="AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw")

# 🔄 嘗試使用 1.5-pro，這是目前最穩定的旗艦模型名稱
model = genai.GenerativeModel('gemini-1.5-pro') 

SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 雲端同步邏輯 ---
def load_data_from_sheets():
    try:
        df = pd.read_csv(CSV_URL)
        return df.to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data_from_sheets()

# --- 第一頁：拍照同步 ---
st.title("📸 拍照建立雲端單字庫")
uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="待辨識照片", use_column_width=True)
    
    if st.button("🚀 開始辨識並同步到雲端"):
        with st.spinner('Gemini 老師正在換眼鏡看清楚一點...'):
            try:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                # 稍微加強提示詞，確保它回傳乾淨的 JSON
                prompt = "Read the English words and Chinese meanings from the image. Return ONLY a JSON list: [{'word':'apple','definition':'蘋果','hint':'a'}]"
                response = model.generate_content([prompt, img])
                
                # 抓取 JSON
                match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if match:
                    new_words = json.loads(match.group())
                    st.session_state.word_bank = new_words
                    st.success(f"✅ 成功辨識 {len(new_words)} 個單字！")
                    st.balloons()
                else:
                    st.error("辨識成功但格式不符，請再試一次。")
            except Exception as e:
                # 顯示錯誤，並提示換個模型名稱試試
                st.error(f"連線出問題了：{str(e)}")
                st.info("💡 老師提示：如果持續出現 404，可能是 Google 伺服器正在維護，請稍後再試。")
