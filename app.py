import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import re

# --- 1. 核心設定 ---
# 你的 API Key
genai.configure(api_key="AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw")

# 自動找尋能用的模型（解決 404 報錯）
@st.cache_resource
def get_working_model():
    models_to_try = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-1.5-pro']
    for m in models_to_try:
        try:
            return genai.GenerativeModel(m)
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_working_model()

# 試算表資訊
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 資料處理 ---
def load_data():
    try:
        return pd.read_csv(CSV_URL).to_dict('records')
    except:
        return []

if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data()

# --- 3. 側邊欄導覽 (這段一定要在最外面) ---
st.sidebar.title("🧑‍🏫 雲端選單")
# 使用 index 確保頁面狀態穩定
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

if st.sidebar.button("🗑️ 清空單字庫"):
    st.session_state.word_bank = []
    st.rerun()

# --- 4. 模式切換邏輯 ---
if "📸 拍照同步題庫" in page:
    st.title("📸 拍照建立題庫")
    st.info(f"🤖 AI 模型狀態：{model.model_name} 已就緒")
    
    uploaded_file = st.file_uploader("上傳照片", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        if st.button("🚀 開始辨識"):
            with st.spinner('辨識中...'):
                try:
                    if img.mode != 'RGB': img = img.convert('RGB')
                    prompt = "Return JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        st.session_state.word_bank = json.loads(match.group())
                        st.success("成功！")
                        st.table(st.session_state.word_bank)
                        st.balloons()
                except Exception as e:
                    st.error(f"錯誤：{e}")

elif "✍️ Lv1. 拼字大挑戰" in page:
    st.title("✍️ 拼字大挑戰")
    if not st.session_state.word_bank:
        st.warning("請先去拍照喔！")
    else:
        st.write("單字列表：")
        st.table(st.session_state.word_bank)

elif "🧠 Lv2. 小六情境測驗" in page:
    st.title("🧠 情境測驗")
    st.write("功能開發中，目前已連動單字庫。")
