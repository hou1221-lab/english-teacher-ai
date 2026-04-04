import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re

# --- 1. 核心設定 ---
genai.configure(api_key="AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw")

# 🔄 自動偵測模型邏輯：解決 404 報錯
def get_working_model():
    # 按照優先順序測試：flash-latest > flash > pro
    models_to_try = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-1.5-pro']
    for m in models_to_try:
        try:
            # 測試模型是否存在
            m_info = genai.get_model(f'models/{m}')
            return genai.GenerativeModel(m)
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash') # 保底

model = get_working_model()

# 你的 Google Sheet 資訊
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
st.title("📸 拍照建立雲端題庫")
st.info(f"🤖 目前使用的 AI 大腦：{model.model_name}")

uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="待辨識照片", use_container_width=True)
    
    if st.button("🚀 開始辨識並同步到雲端"):
        with st.spinner('Gemini 老師正在連線中...'):
            try:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                prompt = "Read the English words and Chinese meanings from the image. Return ONLY a JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                response = model.generate_content([prompt, img])
                
                # 強力過濾 JSON 內容
                match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if match:
                    new_words = json.loads(match.group())
                    st.session_state.word_bank = new_words
                    st.success(f"✅ 成功辨識 {len(new_words)} 個單字！")
                    st.table(new_words) # 顯示出來讓你看
                    st.balloons()
                else:
                    st.error("AI 雖然看懂了，但回傳的筆記格式不對，請再試一次。")
            except Exception as e:
                st.error(f"連線出問題了：{str(e)}")
                st.info("💡 建議：確認 API Key 是否有效，或換一張更清晰的照片。")

# --- 側邊欄 ---
if st.sidebar.button("🗑️ 清空單字"):
    st.session_state.word_bank = []
    st.rerun()
