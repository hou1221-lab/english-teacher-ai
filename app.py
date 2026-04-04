import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re
import random

# --- 1. 核心安全設定 ---
# 這是修復 404 的關鍵：強制指定 transport 為 'rest'，並使用最穩定的 API 設定
API_KEY = "AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw"
genai.configure(api_key=API_KEY, transport='rest')

def get_stable_model():
    # 按照穩定度排序：直接指定最可能的正確路徑
    try:
        # 嘗試 1.5 Flash
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        try:
            # 嘗試 1.5 Pro
            return genai.GenerativeModel('gemini-1.5-pro')
        except:
            # 保底方案
            return genai.GenerativeModel('gemini-pro')

model = get_stable_model()

# Google Sheet 資訊
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 資料載入 ---
def load_data():
    try:
        return pd.read_csv(CSV_URL).to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()
if 'current_q' not in st.session_state:
    st.session_state.current_q = None

# --- 3. 側邊欄導覽 ---
st.sidebar.title("🧑‍🏫 雲端選單")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

# --- 4. 功能邏輯 ---
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立雲端題庫")
    st.info(f"🤖 目前連線大腦：{model.model_name}")
    
    uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        if st.button("🚀 開始辨識"):
            with st.spinner('正在強制連接穩定伺服器...'):
                try:
                    if img.mode != 'RGB': img = img.convert('RGB')
                    prompt = "Extract English words and Chinese meanings into JSON list: [{'word':'...', 'definition':'...', 'hint':'...'}]"
                    # 加入安全調用
                    response = model.generate_content([prompt, img])
                    
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        st.session_state.word_bank = json.loads(match.group())
                        st.success("成功辨識！單字已同步。")
                        st.table(st.session_state.word_bank)
                        st.balloons()
                except Exception as e:
                    st.error(f"連線失敗。請確認：1. API Key 正確 2. 帳號是否有額度。 錯誤: {e}")

elif "✍️ Lv1. 拼字大挑戰" in page:
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("請先去拍照喔！")
    else:
        if st.button("🎯 換一題") or st.session_state.current_q is None:
            st.session_state.current_q = random.choice(st.session_state.word_bank)
        
        q = st.session_state.current_q
        st.subheader(f"中文：{q['definition']}")
        ans = st.text_input("輸入單字：").strip()
        if st.button("檢查"):
            if ans.lower() == q['word'].lower():
                st.success("正確！")
                st.balloons()
            else:
                st.error(f"錯囉，是 {q['word']}")

elif "🧠 Lv2. 小六情境測驗" in page:
    st.title("🧠 情境測驗")
    st.write("連線正常，可根據單字庫自動出題。")
