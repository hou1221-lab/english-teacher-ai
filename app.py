import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re
import random

# --- 1. 核心安全設定 ---
# 這是您的新金鑰 (AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI)
API_KEY = st.secrets.get("GEMINI_API_KEY") or "AIzaSyCAHiqabmlZ1HVB4SLeyhsoqjU-HY05wiI"

# 強制走 rest 穩定模式，避開 404
genai.configure(api_key=API_KEY, transport='rest')
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="孩子英文學習小老師", layout="centered", page_icon="📝")

# --- 🎯 自訂 CSS：強制放大輸入框文字 🎯 ---
st.markdown("""
    <style>
    /* 放大所有文字輸入框的字體 */
    .stTextInput input {
        font-size: 24px !important;
        height: 50px !important;
        font-weight: bold !important;
    }
    /* 放大題目中文的字體 */
    .big-font {
        font-size: 28px !important;
        font-weight: bold !important;
        color: #31333F;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化單字庫
if 'word_bank' not in st.session_state:
    st.session_state.word_bank = []
if 'quiz_idx' not in st.session_state:
    st.session_state.quiz_idx = 0

# --- 2. 側邊欄選單 ---
st.sidebar.title("🎒 學習選單")
page = st.sidebar.radio("切換頁面", [
    "🔒 家長拍照區", 
    "✍️ 第一頁：拼字練習 (字體放大)", 
    "🎮 第二頁：中文選英文 (四選一)",
    "🧠 第三頁：題庫選擇題 (四選一)"
])

if st.sidebar.button("🗑️ 重設題庫"):
    st.session_state.word_bank = []
    st.session_state.quiz_idx = 0
    st.rerun()

# --- 3. 家長拍照區 (隱藏圖片) ---
if page == "🔒 家長拍照區":
    st.title("🔒 家長出題專區")
    st.info("請上傳單字照片，辨識後請切換頁面給孩子練習 (照片會自動遮蔽)。")
    
    uploaded_file = st.file_uploader("請選擇照片...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        if st.button("🚀 開始辨識並隱藏圖片"):
            img = Image.open(uploaded_file)
            with st.spinner('AI 老師正在讀取單字...'):
                try:
                    # 強制轉成 RGB 確保相容性
                    if img.mode != 'RGB': img = img.convert('RGB')
                    
                    # 傳送指令給 AI
                    prompt = "Extract words. Return ONLY plain JSON list: [{'word':'英文','definition':'中文','hint':'首字母'}]"
                    response = model.generate_content([prompt, img])
                    
                    # 解析 JSON
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        words = json.loads(match.group())
                        # 🛡️ 安全檢查：確保 hint 存在
                        for w in words:
                            if 'hint' not in w or not w['hint']:
                                w['hint'] = w['word'][0].lower() if w['word'] else ""
                                
                        st.session_state.word_bank = words
                        st.success(f"🎉 成功！辨識出 {len(words)} 個單字，圖片已隱藏。")
                        st.balloons()
                    else:
                        st.error("辨識成功但格式不對。")
                except Exception as e:
                    st.error(f"連線失敗：{e}")

# --- 4. 第一頁：拼字填空題 (字體放大) ---
elif page == "✍️ 第一頁：拼字練習 (字體放大)":
    st.title("✍️ 拼字填空挑戰")
    if not st.session_state.word_bank:
        st.warning("⚠️ 題庫是空的，請家長先拍照出題喔！")
    else:
        st.write("請看中文，打出正確的英文單字：")
        
        # 10 個單字就會生成 10 題
        correct_count = 0
        for i, item in enumerate(st.session_state.word_bank):
            # 題目中文 (放大)
            st.markdown(f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>", unsafe_allow_html=True)
            
            # 提示如 a _ _ _ _
            placeholder = f"{item['word'][0].upper()} {'_ ' * (len(item['word'])-1)}"
            
            # 孩子輸入框 (字體已用 CSS 放大)
            child_ans = st.text_input(f"提示：{placeholder}", key=f"spell_{i}").strip()
            
            if child_ans.lower() == item['word'].lower():
                st.success("🎉 正確！")
                correct_count += 1
        
        if correct_count == len(st.session_state.word_bank):
            st.balloons()

# --- 5. 第二頁：中文選英文 (四選一) ---
elif page == "🎮 第二頁：中文選英文 (四選一)":
    st.title("🎮 中文選英文挑战")
    
    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 題庫單字不足 4 個，無法生成四選一選項。")
    else:
        # 隨機選一題
        if 'c2e_idx' not in st.session_state or st.button("🎲 換一題"):
            st.session_state.c2e_idx = random.randint(0, len(st.session_state.word_bank)-1)
            
            correct_item = st.session_state.word_bank[st.session_state.c2e_idx]
            correct_ans = correct_item['word']
            
            # 製作干擾項 (抓取其他英文單字)
            others = [w['word'] for w in st.session_state.word_bank if w['word'] != correct_ans]
            wrong_choices = random.sample(others, min(len(others), 3))
            
            # 組合選項並打亂
            choices = wrong_choices + [correct_ans]
            random.shuffle(choices)
            st.session_state.c2e_choices = choices

        correct_item = st.session_state.word_bank[st.session_state.c2e_idx]
        
        # 顯示題目中文 (放大)
        st.markdown(f"<p class='big-font'>請問 **{correct_item['definition']}** 的英文是？</p>", unsafe_allow_html=True)
        
        # 製作選擇按鈕 (直排)
        user_choice = st.radio("你的選擇：", st.session_state.c2e_choices, key="c2e_radio")
        
        if st.button("檢查答案"):
            if user_choice == correct_item['word']:
                st.success(f"✅ 沒錯！就是 {correct_item['word']}！")
                st.balloons()
            else:
                st.error("❌ 選錯了，再試一次喔！")

# --- 6. 第三頁：題庫選擇題 (四選一) ---
elif page == "🧠 第三頁：題庫選擇題 (四選一)":
    st.title("🧠 題庫總複習選擇題")
    
    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 題庫單字不足 4 個，無法練習。")
    else:
        # 隨機選一題 Correct Answer
        if 'quiz_data' not in st.session_state or st.button("🎲 下一題挑戰"):
            correct_idx = random.randint(0, len(st.session_state.word_bank)-1)
            correct_item = st.session_state.word_bank[correct_idx]
            
            # Correct Choice
            correct_word = correct_item['word']
            
            # Wrong Choices (從同一個題庫抓)
            wrong_words = [w['word'] for w in st.session_state.word_bank if w['word'] != correct_word]
            distractors = random.sample(wrong_words, min(len(wrong_words), 3))
            
            # 組合選項並打亂
            options = distractors + [correct_word]
            random.shuffle(options)
            
            st.session_state.quiz_data = {
                'correct_word': correct_word,
                'definition': correct_item['definition'],
                'options': options
            }

        q = st.session_state.quiz_data
        
        # 顯示題目中文 (放大)
        st.markdown(f"<p class='big-font'>請問 **{q['definition']}** 是哪個單字？</p>", unsafe_allow_html=True)
        
        # 製作選擇按鈕
        user_choice = st.radio("孩子，請選出正確的單字：", q['options'], key="quiz_radio")
        
        if st.button("提交答案"):
            if user_choice == q['correct_word']:
                st.success("🎉 太棒了！完完全全正確！")
                st.balloons()
            else:
                st.error(f"差一點點！答案應該是：{q['correct_word']}")
