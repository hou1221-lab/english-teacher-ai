import streamlit as st
import pandas as pd
import random
import re
from PIL import Image
import pytesseract

# =========================================
# 1. 基本設定
# =========================================
st.set_page_config(page_title="孩子英文學習機", layout="centered", page_icon="📝")

st.markdown("""
<style>
.stTextInput input {
    font-size: 30px !important;
    height: 60px !important;
    font-weight: bold !important;
}
.big-font {
    font-size: 30px !important;
    font-weight: bold !important;
    line-height: 1.6;
}
div[data-baseweb="radio"] label {
    font-size: 22px !important;
    font-weight: bold !important;
}
.small-note {
    font-size: 18px !important;
    color: #666;
}
</style>
""", unsafe_allow_html=True)

# =========================================
# 2. Session State 初始化
# =========================================
if "word_bank" not in st.session_state:
    st.session_state.word_bank = []

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# =========================================
# 3. 工具函式
# =========================================
def clean_text(text):
    """清理 OCR 結果"""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def parse_ocr_lines(text):
    """
    嘗試把 OCR 結果拆成：
    英文 中文
    例如：
    apple 蘋果
    banana 香蕉
    """
    results = []
    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)
        if not line:
            continue

        # 抓英文開頭 + 後面中文
        # 例：apple 蘋果
        match = re.match(r"^([A-Za-z][A-Za-z\s\-']*)\s+(.+)$", line)
        if match:
            eng = clean_text(match.group(1)).lower()
            chi = clean_text(match.group(2))

            # 過濾太奇怪的資料
            if eng and chi and len(eng) <= 30:
                results.append({"word": eng, "definition": chi})

    # 去重複
    unique = []
    seen = set()
    for item in results:
        key = (item["word"], item["definition"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def get_hint(word):
    """例如 apple -> a _ _ _ _"""
    if len(word) <= 1:
        return word
    return word[0] + " " + " ".join(["_"] * (len(word) - 1))


def generate_choices_from_definitions(correct_definition, word_bank, total_choices=4):
    """給英文，選正確中文"""
    all_defs = [w["definition"] for w in word_bank if w["definition"] != correct_definition]
    distractors = random.sample(all_defs, min(total_choices - 1, len(all_defs)))
    choices = distractors + [correct_definition]
    random.shuffle(choices)
    return choices


def generate_choices_from_words(correct_word, word_bank, total_choices=4):
    """給中文，選正確英文"""
    all_words = [w["word"] for w in word_bank if w["word"] != correct_word]
    distractors = random.sample(all_words, min(total_choices - 1, len(all_words)))
    choices = distractors + [correct_word]
    random.shuffle(choices)
    return choices


# =========================================
# 4. 側邊欄
# =========================================
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio(
    "切換頁面",
    [
        "📷 家長上傳區（照片辨識 / 手動輸入）",
        "✍️ 第一頁：中文提示拼英文",
        "🎯 第二頁：英文選中文",
        "🧠 第三頁：綜合10題挑戰"
    ]
)

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    st.session_state.quiz_submitted = False
    st.rerun()

# =========================================
# 5. 家長上傳區
# =========================================
if page == "📷 家長上傳區（照片辨識 / 手動輸入）":
    st.title("📷 家長上傳區")
    st.markdown("<p class='small-note'>你可以上傳單字表照片，也可以手動補充單字。</p>", unsafe_allow_html=True)

    # ---- 照片上傳 OCR ----
    st.subheader("① 上傳單字表照片")
    uploaded_file = st.file_uploader("請上傳圖片（jpg / png / jpeg）", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="已上傳圖片", use_container_width=True)

        if st.button("🔍 辨識照片中的單字"):
            try:
                # 若是 Windows 且已安裝 Tesseract，可取消下面註解並改成你的路徑
                # pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

                text = pytesseract.image_to_string(image, lang="eng")
                parsed_words = parse_ocr_lines(text)

                if parsed_words:
                    added = 0
                    existing_keys = {(x["word"], x["definition"]) for x in st.session_state.word_bank}

                    for item in parsed_words:
                        key = (item["word"], item["definition"])
                        if key not in existing_keys:
                            st.session_state.word_bank.append(item)
                            existing_keys.add(key)
                            added += 1

                    st.success(f"辨識完成，新增 {added} 筆單字。")
                    st.text_area("OCR 原始辨識結果", text, height=200)
                else:
                    st.warning("沒有成功辨識出『英文 + 中文』格式。你可以改用手動輸入補上。")
                    st.text_area("OCR 原始辨識結果", text, height=200)

            except Exception as e:
                st.error(f"OCR 辨識失敗：{e}")
                st.info("提醒：這個功能需要先安裝 Tesseract OCR。")

    # ---- 手動輸入 ----
    st.subheader("② 手動加入單字")
    with st.form("add_word", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            eng = st.text_input("英文單字")
        with c2:
            chi = st.text_input("中文意思")

        submitted = st.form_submit_button("➕ 加入題庫")
        if submitted:
            eng = clean_text(eng).lower()
            chi = clean_text(chi)

            if eng and chi:
                st.session_state.word_bank.append({"word": eng, "definition": chi})
                st.success(f"已加入：{eng} / {chi}")
            else:
                st.error("英文和中文都不能空白。")

    # ---- 顯示題庫 ----
    st.subheader("③ 目前題庫")
    if st.session_state.word_bank:
        df = pd.DataFrame(st.session_state.word_bank)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前還沒有單字。")

# =========================================
# 6. 第一頁：中文提示拼英文
#    例：蘋果 a _ _ _ _
# =========================================
elif page == "✍️ 第一頁：中文提示拼英文":
    st.title("✍️ 中文提示拼英文")

    if not st.session_state.word_bank:
        st.warning("請先到家長上傳區建立題庫。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>",
                unsafe_allow_html=True
            )

            hint = get_hint(item["word"])
            ans = st.text_input(
                f"提示：{hint}",
                key=f"spell_{i}"
            ).strip().lower()

            if ans:
                if ans == item["word"].lower():
                    st.success("✅ 正確")
                else:
                    st.error(f"❌ 再試一次，提示是：{hint}")

# =========================================
# 7. 第二頁：英文選中文
#    例：apple -> 選 蘋果
# =========================================
elif page == "🎯 第二頁：英文選中文":
    st.title("🎯 英文選中文")

    if len(st.session_state.word_bank) < 2:
        st.warning("至少需要 2 個單字才適合做選擇題。")
    else:
        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['word']}</p>",
                unsafe_allow_html=True
            )

            choices = generate_choices_from_definitions(item["definition"], st.session_state.word_bank)
            choice = st.radio("請選出正確中文：", choices, key=f"mc_def_{i}")

            if st.button("檢查答案", key=f"btn_def_{i}"):
                if choice == item["definition"]:
                    st.success("🎉 答對了")
                else:
                    st.error(f"❌ 正確答案是：{item['definition']}")

# =========================================
# 8. 第三頁：綜合挑戰
#    題目數 = 題庫數，例如 10 個字就出 10 題
#    給中文，選正確英文
# =========================================
elif page == "🧠 第三頁：綜合10題挑戰":
    st.title("🧠 綜合挑戰")

    if len(st.session_state.word_bank) < 4:
        st.warning("至少需要 4 個單字，才能進行四選一綜合測驗。")
    else:
        st.markdown(
            f"<p class='small-note'>目前題庫共有 {len(st.session_state.word_bank)} 個單字，將出 {len(st.session_state.word_bank)} 題。</p>",
            unsafe_allow_html=True
        )

        score = 0

        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：哪一個英文是「{item['definition']}」？</p>",
                unsafe_allow_html=True
            )

            choices = generate_choices_from_words(item["word"], st.session_state.word_bank)
            user_choice = st.radio("請選擇正確英文：", choices, key=f"quiz_{i}")

            if user_choice == item["word"]:
                score += 1

        if st.button("📊 送出測驗"):
            st.success(f"你的分數：{score} / {len(st.session_state.word_bank)}")

            if score == len(st.session_state.word_bank):
                st.balloons()
                st.success("太厲害了，全對！")
