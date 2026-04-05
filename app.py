import streamlit as st
import random
import pandas as pd
import re
from pypdf import PdfReader

# =========================================
# 1. 基本設定
# =========================================
st.set_page_config(
    page_title="孩子英文學習機",
    layout="centered",
    page_icon="📝"
)

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 22px !important;
}

h1 {
    font-size: 46px !important;
    font-weight: 900 !important;
}
h2 {
    font-size: 38px !important;
    font-weight: 800 !important;
}
h3 {
    font-size: 30px !important;
    font-weight: 800 !important;
}

.big-font {
    font-size: 40px !important;
    font-weight: 900 !important;
    line-height: 1.7 !important;
    margin-bottom: 12px !important;
}

.normal-font {
    font-size: 24px !important;
    line-height: 1.6 !important;
}

.stTextInput input {
    font-size: 30px !important;
    height: 68px !important;
    font-weight: bold !important;
}

textarea {
    font-size: 22px !important;
}

div[data-baseweb="radio"] label {
    font-size: 28px !important;
    font-weight: bold !important;
    line-height: 1.8 !important;
}

.stButton button {
    font-size: 24px !important;
    font-weight: bold !important;
    padding: 12px 20px !important;
    border-radius: 12px !important;
}

button[data-baseweb="tab"] {
    font-size: 22px !important;
    font-weight: bold !important;
}

section[data-testid="stSidebar"] * {
    font-size: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================
# 2. Session State 初始化
# =========================================
if "word_bank" not in st.session_state:
    st.session_state.word_bank = []

if "challenge_wrong" not in st.session_state:
    st.session_state.challenge_wrong = []

if "challenge_submitted" not in st.session_state:
    st.session_state.challenge_submitted = False

if "challenge_score" not in st.session_state:
    st.session_state.challenge_score = 0

# =========================================
# 3. 工具函式
# =========================================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())

def deduplicate_words(word_list):
    seen = set()
    result = []
    for item in word_list:
        word = clean_text(item.get("word", "")).lower()
        definition = clean_text(item.get("definition", ""))
        if word and definition:
            key = (word, definition)
            if key not in seen:
                seen.add(key)
                result.append({"word": word, "definition": definition})
    return result

def parse_bulk_text(text):
    """
    支援：
    apple 蘋果
    banana 香蕉

    或：
    apple,蘋果
    banana,香蕉

    或：
    apple\t蘋果
    """
    results = []
    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)
        if not line:
            continue

        parts = None

        if "," in line:
            parts = [x.strip() for x in line.split(",", 1)]
        elif "\t" in line:
            parts = [x.strip() for x in line.split("\t", 1)]
        else:
            parts = line.split(" ", 1)

        if len(parts) == 2:
            eng = clean_text(parts[0]).lower()
            chi = clean_text(parts[1])

            if re.fullmatch(r"[A-Za-z][A-Za-z\\-\\s']*", eng):
                results.append({"word": eng, "definition": chi})

    return deduplicate_words(results)

def get_hint(word):
    word = word.strip()
    if len(word) <= 1:
        return word
    return f"{word[0]} " + " ".join(["_"] * (len(word) - 1))

def make_choice_list(correct_value, pool, key_name):
    others = [item[key_name] for item in pool if item[key_name] != correct_value]
    distractors = random.sample(others, min(3, len(others)))
    choices = distractors + [correct_value]
    random.shuffle(choices)
    return choices

def import_words(new_words):
    st.session_state.word_bank.extend(new_words)
    st.session_state.word_bank = deduplicate_words(st.session_state.word_bank)

def load_words_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def reset_challenge_results():
    st.session_state.challenge_wrong = []
    st.session_state.challenge_submitted = False
    st.session_state.challenge_score = 0

def generate_sentence(word, definition):
    """
    第三頁用的句子題。
    優先依中文意思決定句子，抓不到時用通用句。
    """
    text = clean_text(definition)

    rules = [
        (["帳目", "帳戶", "戶頭"], "We check the money in the ______."),
        (["意外", "事故"], "It was an ______ on the road."),
        (["冒險"], "The trip was a great ______."),
        (["活動"], "The school has a fun ______ today."),
        (["優點", "好處"], "Reading is a big ______."),
        (["欽佩", "欣賞"], "I really ______ her courage."),
        (["疼痛"], "I have an ______ in my leg."),
        (["達成", "成就"], "She worked hard to ______ her goal."),
        (["接受", "可接受"], "This answer is ______ to me."),
        (["一致", "符合", "同意"], "I ______ with your idea."),
        (["說明", "解釋"], "The teacher gives an ______ in class."),
        (["演員"], "The ______ is very famous."),
        (["行動", "動作"], "The hero takes quick ______."),
        (["活躍"], "She is very ______ in class."),
        (["住址", "地址"], "Please write your home ______."),
    ]

    for keywords, sentence in rules:
        if any(k in text for k in keywords):
            return sentence

    # 預設通用句
    return f"This word means: {definition}. Choose the best answer for the ______."

# =========================================
# 4. 側邊欄
# =========================================
st.sidebar.title("🎒 學習控制台")
page = st.sidebar.radio(
    "切換頁面",
    [
        "📝 家長建立題庫",
        "✍️ 第一頁：中文提示拼英文",
        "🎯 第二頁：英文選中文",
        "🧠 第三頁：句子選英文",
        "📚 錯題本"
    ]
)

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    reset_challenge_results()
    st.rerun()

# =========================================
# 5. 家長建立題庫
# =========================================
if page == "📝 家長建立題庫":
    st.title("📝 家長建立題庫")
    st.markdown("<p class='normal-font'>可以單筆輸入、整批貼上，或直接上傳 PDF 單字表。</p>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["單筆輸入", "整批貼上", "PDF 匯入"])

    with tab1:
        with st.form("single_add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                eng = st.text_input("英文單字")
            with col2:
                chi = st.text_input("中文意思")

            submitted = st.form_submit_button("➕ 加入題庫")
            if submitted:
                eng = clean_text(eng).lower()
                chi = clean_text(chi)

                if eng and chi:
                    import_words([{"word": eng, "definition": chi}])
                    st.success(f"已加入：{eng} / {chi}")
                else:
                    st.error("英文和中文都不能空白。")

    with tab2:
        st.markdown("<p class='normal-font'>請一行一筆，例如：</p>", unsafe_allow_html=True)
        st.code("apple 蘋果\nbanana 香蕉\norange 橘子\naccount 帳目、說明")
        st.markdown("<p class='normal-font'>也支援逗號格式：</p>", unsafe_allow_html=True)
        st.code("apple,蘋果\nbanana,香蕉")

        bulk_text = st.text_area("請貼上單字表", height=240)

        if st.button("📥 匯入整批單字"):
            parsed = parse_bulk_text(bulk_text)
            if parsed:
                import_words(parsed)
                st.success(f"成功匯入 {len(parsed)} 筆單字。")
            else:
                st.error("格式不正確，請用「英文 空格 中文」或「英文,中文」。")

    with tab3:
        st.markdown("<p class='normal-font'>上傳 PDF 後，系統會先把文字抓出來，再轉成題庫。</p>", unsafe_allow_html=True)
        st.markdown("<p class='normal-font'>PDF 內容最好是這種格式：</p>", unsafe_allow_html=True)
        st.code("apple 蘋果\nbanana 香蕉\naccord 一致、符合\nacceptable 可接受的，合意的")

        pdf_file = st.file_uploader("上傳 PDF 單字表", type=["pdf"], key="pdf_uploader")

        if pdf_file:
            try:
                extracted_text = load_words_from_pdf(pdf_file)
                st.text_area("📖 PDF 解析內容（可先檢查）", extracted_text, height=260, key="pdf_text_preview")

                if st.button("📥 將 PDF 內容轉成題庫"):
                    parsed = parse_bulk_text(extracted_text)
                    if parsed:
                        import_words(parsed)
                        st.success(f"成功匯入 {len(parsed)} 筆單字。")
                    else:
                        st.error("無法解析成題庫，請確認 PDF 每行是『英文 中文』或『英文,中文』。")
            except Exception as e:
                st.error(f"PDF 讀取失敗：{e}")

    st.subheader("📋 目前題庫清單")
    if st.session_state.word_bank:
        df = pd.DataFrame(st.session_state.word_bank)
        st.dataframe(df, use_container_width=True)

        csv_data = pd.DataFrame(st.session_state.word_bank).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ 下載題庫 CSV",
            data=csv_data,
            file_name="word_bank.csv",
            mime="text/csv"
        )
    else:
        st.info("目前還沒有單字。")

# =========================================
# 6. 第一頁：中文提示拼英文
# =========================================
elif page == "✍️ 第一頁：中文提示拼英文":
    st.title("✍️ 中文提示拼英文")

    if not st.session_state.word_bank:
        st.warning("⚠️ 題庫空空的，請先到家長建立題庫。")
    else:
        st.markdown("<p class='normal-font'>看到中文後，自己拼出英文單字。</p>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['definition']}</p>",
                unsafe_allow_html=True
            )

            hint = get_hint(item["word"])
            ans = st.text_input(f"提示：{hint}", key=f"spell_{i}").strip().lower()

            if ans:
                if ans == item["word"]:
                    st.success("✅ 正確！")
                else:
                    st.error(f"❌ 再試一次。提示：{hint}")

# =========================================
# 7. 第二頁：英文選中文
# =========================================
elif page == "🎯 第二頁：英文選中文":
    st.title("🎯 英文選中文")

    if len(st.session_state.word_bank) < 2:
        st.warning("⚠️ 至少要 2 個單字才能做選擇題。")
    else:
        st.markdown("<p class='normal-font'>看到英文，選出正確中文。</p>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.word_bank):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{item['word']}</p>",
                unsafe_allow_html=True
            )

            correct = item["definition"]
            options = make_choice_list(correct, st.session_state.word_bank, "definition")

            user_choice = st.radio("請選擇：", options, key=f"q2_{i}")
            if st.button("檢查答案", key=f"btn2_{i}"):
                if user_choice == correct:
                    st.success("🎉 太棒了！")
                else:
                    st.error(f"❌ 正確答案是：{correct}")

# =========================================
# 8. 第三頁：句子選英文（一次列出全部）
# =========================================
elif page == "🧠 第三頁：句子選英文":
    st.title("🧠 題庫總複習")

    if len(st.session_state.word_bank) < 4:
        st.warning("⚠️ 至少要 4 個單字才能做四選一。")
    else:
        st.markdown(
            "<p class='normal-font'>請根據句子內容，選出最適合的英文單字。全部作答後，再按一次按鈕結算分數。</p>",
            unsafe_allow_html=True
        )

        score = 0
        wrong_list = []

        for i, item in enumerate(st.session_state.word_bank):
            sentence = generate_sentence(item["word"], item["definition"])
            correct = item["word"]
            options = make_choice_list(correct, st.session_state.word_bank, "word")

            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{sentence}</p>",
                unsafe_allow_html=True
            )

            user_choice = st.radio("請選擇：", options, key=f"q3_{i}")

            if user_choice == correct:
                score += 1
            else:
                wrong_list.append({
                    "題號": i + 1,
                    "句子": sentence,
                    "中文意思": item["definition"],
                    "你的答案": user_choice,
                    "正確答案": correct
                })

        if st.button("📊 送出結算分數"):
            st.session_state.challenge_score = score
            st.session_state.challenge_wrong = wrong_list
            st.session_state.challenge_submitted = True
            st.rerun()

        if st.session_state.challenge_submitted:
            st.success(f"總分：{st.session_state.challenge_score} / {len(st.session_state.word_bank)}")

            if st.session_state.challenge_score == len(st.session_state.word_bank):
                st.balloons()
                st.success("全部答對！")

            if st.session_state.challenge_wrong:
                st.subheader("❌ 本次錯題")
                wrong_df = pd.DataFrame(st.session_state.challenge_wrong)
                st.dataframe(wrong_df, use_container_width=True)

# =========================================
# 9. 錯題本
# =========================================
elif page == "📚 錯題本":
    st.title("📚 錯題本")

    if st.session_state.challenge_wrong:
        st.markdown("<p class='normal-font'>這裡會顯示最近一次第三頁答錯的題目。</p>", unsafe_allow_html=True)
        wrong_df = pd.DataFrame(st.session_state.challenge_wrong)
        st.dataframe(wrong_df, use_container_width=True)

        csv_data = wrong_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ 下載錯題本 CSV",
            data=csv_data,
            file_name="wrong_answers.csv",
            mime="text/csv"
        )
    else:
        st.info("目前還沒有錯題紀錄。先去第三頁做一輪吧。")
