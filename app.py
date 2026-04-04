import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import random
import pandas as pd
from datetime import datetime

# --- 1. 核心設定 ---
# 填入你的 Gemini API Key
genai.configure(api_key="AIzaSyAxh-ENdvEGfmhmvZyl6Pj9SzJ-flrN4hw")
model = genai.GenerativeModel('gemini-1.5-flash')

# 填入你的 Google 試算表 ID
SHEET_ID = "1Katc3p0WaavcPSFQU1pBX8QovS-wmfWbzm6M3ifiUJo"
# 這是讀取 Google Sheets 的祕技網址
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Gemini 雲端小老師", layout="centered", page_icon="🧑‍🏫")

# --- 2. 雲端同步邏輯 ---
def load_data_from_sheets():
    try:
        # 從 Google Sheets 抓取資料
        df = pd.read_csv(CSV_URL)
        # 轉成我們程式用的格式
        data = df.to_dict('records')
        return data
    except:
        return []

# 初始化 Session State
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = load_data_from_sheets()
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = {}

# --- 3. 側邊欄控制 ---
st.sidebar.title("🧑‍🏫 Gemini 雲端導覽")
page = st.sidebar.radio("請選擇模式", ["📸 拍照同步題庫", "✍️ Lv1. 拼字大挑戰", "🧠 Lv2. 小六情境測驗"])

# --- 第一頁：拍照同步 ---
if page == "📸 拍照同步題庫":
    st.title("📸 拍照建立雲端單字庫")
    st.info("提示：在這裡上傳後，其他裝置打開網頁就能看到同樣的單字！")
    
    uploaded_file = st.file_uploader("請上傳單字照片", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="待辨識照片", use_column_width=True)
        
        if st.button("🚀 開始辨識並同步到雲端"):
            with st.spinner('Gemini 老師正在分析中...'):
                prompt = "請讀取圖片中的英文單字與中文。只回傳 JSON 列表：[{'word':'英文單字','definition':'中文意思','hint':'首字母'}]"
                try:
                    response = model.generate_content([prompt, img])
                    raw_text = response.text.replace('```json', '').replace('```', '').strip()
                    new_words = json.loads(raw_text)
                    
                    # 更新當前記憶
                    st.session_state.word_bank = new_words
                    st.session_state.quiz_data = [] # 重置考題
                    st.success(f"✅ 成功辨識 {len(new_words)} 個單字！")
                    st.balloons()
                except:
                    st.error("辨識失敗，請確認照片清晰度。")

# --- 第二頁：拼字練習 ---
elif page == "✍️ Lv1. 拼字大挑戰":
    st.title("✍️ Lv1. 拼字練習")
    
    if not st.session_state.word_bank:
        st.warning("雲端目前沒有單字，請先去拍照上傳！")
    else:
        score = 0
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(f"### 第 {i+1} 題：")
            st.markdown(f"<h1 style='color: #1E88E5; font-size: 60px;'>{item['definition']}</h1>", unsafe_allow_html=True)
            
            user_ans = st.text_input(f"請輸入英文 (提示：{item['hint']}...)", key=f"p1_ans_{i}").strip().lower()
            if user_ans == item['word'].lower():
                st.success("✨ 拼字正確！")
                score += 1
            st.divider()
        st.sidebar.metric("目前得分", f"{score} / {len(st.session_state.word_bank)}")

# --- 第三頁：隨機情境測驗 ---
elif page == "🧠 Lv2. 小六情境測驗":
    st.title("🧠 Lv2. 隨機情境挑戰")
    
    if not st.session_state.word_bank:
        st.warning("雲端目前沒有單字，請先去拍照上傳！")
    else:
        if not st.session_state.quiz_data:
            shuffled = list(st.session_state.word_bank)
            random.shuffle(shuffled)
            st.session_state.quiz_data = shuffled

        for i, item in enumerate(st.session_state.quiz_data):
            word = item['word']
            with st.expander(f"🎁 題目 {i+1} (點開挑戰)", expanded=(i in st.session_state.quiz_results)):
                q_key = f"quiz_q_{word}"
                if q_key not in st.session_state:
                    with st.spinner('AI 正在出題...'):
                        p = f"請針對單字 '{word}' 出一個適合小六程度的簡單英文填空題，單字處用 '____' 代替。只需回傳英文句子。"
                        st.session_state[q_key] = model.generate_content(p).text.strip()
                
                st.markdown(f"<h2 style='line-height: 1.5;'>{st.session_state[q_key]}</h2>", unsafe_allow_html=True)
                
                # 產生選項
                others = [x['word'] for x in st.session_state.word_bank if x['word'] != word]
                opts = sorted([word] + random.sample(others, min(len(others), 2)))
                
                choice = st.radio("選出正確答案：", opts, key=f"p2_r_{i}", index=None)
                if choice:
                    if choice == word:
                        st.success(f"🎉 正確！這題考的是：{word} ({item['definition']})")
                        st.session_state.quiz_results[i] = True
                    else:
                        st.error("❌ 答錯囉！")

# 全域清除
if st.sidebar.button("🗑️ 清空所有單字"):
    st.session_state.clear()
    st.rerun()