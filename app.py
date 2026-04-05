import streamlit as st
import pandas as pd
import random
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
html, body, [class*="css"] {
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

.option-font {
    font-size: 28px !important;
    font-weight: bold !important;
    line-height: 1.8 !important;
    margin: 6px 0;
}

.stTextInput input {
    font-size: 30px !important;
    height: 68px !important;
    font-weight: bold !important;
}

textarea {
    font-size: 22px !important;
}

.stSelectbox label {
    font-size: 24px !important;
    font-weight: bold !important;
}

.stSelectbox div[data-baseweb="select"] * {
    font-size: 22px !important;
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
defaults = {
    "word_bank": [],
    "page2_questions": [],
    "page3_questions": [],
    "page2_signature": "",
    "page3_signature": "",
    "page2_submitted": False,
    "page3_submitted": False,
    "page2_score": 0,
    "page3_score": 0,
    "page2_wrong": [],
    "page3_wrong": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================
# 3. 工具函式
# =========================================
def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())

def normalize_word(word):
    return clean_text(word).lower()

def deduplicate_words(word_list):
    seen = set()
    result = []
    for item in word_list:
        word = normalize_word(item.get("word", ""))
        definition = clean_text(item.get("definition", ""))
        example = clean_text(item.get("example", ""))

        if word and definition:
            key = (word, definition, example)
            if key not in seen:
                seen.add(key)
                result.append({
                    "word": word,
                    "definition": definition,
                    "example": example
                })
    return result

def parse_bulk_text(text):
    """
    支援格式：
    1) word 中文
    2) word,中文
    3) word,中文,例句
    4) word\t中文\t例句
    """
    results = []
    lines = text.split("\n")

    for line in lines:
        line = clean_text(line)
        if not line:
            continue

        parts = None

        if "\t" in line:
            parts = [x.strip() for x in line.split("\t")]
        elif "," in line:
            parts = [x.strip() for x in line.split(",")]
        else:
            parts = line.split(" ", 1)

        if len(parts) >= 2:
            eng = normalize_word(parts[0])
            chi = clean_text(parts[1])
            example = clean_text(parts[2]) if len(parts) >= 3 else ""

            if re.fullmatch(r"[A-Za-z][A-Za-z\-\s']*", eng):
                results.append({
                    "word": eng,
                    "definition": chi,
                    "example": example
                })

    return deduplicate_words(results)

def get_hint(word):
    word = word.strip()
    if len(word) <= 1:
        return word
    return f"{word[0]} " + " ".join(["_"] * (len(word) - 1))

def import_words(new_words):
    st.session_state.word_bank.extend(new_words)
    st.session_state.word_bank = deduplicate_words(st.session_state.word_bank)
    refresh_all_question_sets()

def load_words_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def get_bank_signature(word_bank):
    parts = []
    for item in word_bank:
        parts.append(
            f"{item.get('word','')}|{item.get('definition','')}|{item.get('example','')}"
        )
    return "||".join(parts)

def build_fixed_choices(correct_value, all_values, seed_text):
    unique_pool = [v for v in all_values if v != correct_value]
    rng = random.Random(seed_text)
    unique_pool = list(dict.fromkeys(unique_pool))
    rng.shuffle(unique_pool)

    distractors = unique_pool[:3]
    choices = distractors + [correct_value]
    rng.shuffle(choices)

    while len(choices) < 4:
        choices.append("（無）")

    return choices[:4]

def format_options_numbered(options):
    return [f"{i+1}. {opt}" for i, opt in enumerate(options)]

def extract_option_value(label_text):
    if ". " in label_text:
        return label_text.split(". ", 1)[1]
    return label_text

def normalize_example_sentence(example, word):
    example = clean_text(example)
    word = normalize_word(word)

    if not example:
        return ""

    if "____" in example or "______" in example:
        return example

    # 若例句中含有單字，替換成空格
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    if pattern.search(example):
        return pattern.sub("______", example)

    return example

def build_page2_questions(word_bank):
    """
    第二頁：英文選中文
    固定題目、固定選項順序
    """
    signature = get_bank_signature(word_bank)
    all_defs = [item["definition"] for item in word_bank]
    questions = []

    for idx, item in enumerate(word_bank):
        seed_text = f"page2::{signature}::{idx}::{item['word']}"
        choices = build_fixed_choices(item["definition"], all_defs, seed_text)

        questions.append({
            "word": item["word"],
            "definition": item["definition"],
            "choices": choices
        })

    return questions, signature

def build_page3_questions(word_bank):
    """
    第三頁：
    - 有 example -> 句子填空選英文
    - 沒 example -> 中文意思選英文
    一樣全部使用目前題庫的單字
    """
    signature = get_bank_signature(word_bank)
    all_words = [item["word"] for item in word_bank]
    questions = []

    for idx, item in enumerate(word_bank):
        seed_text = f"page3::{signature}::{idx}::{item['word']}"
        choices = build_fixed_choices(item["word"], all_words, seed_text)
        sentence = normalize_example_sentence(item.get("example", ""), item["word"])

        if sentence:
            prompt = sentence
            qtype = "sentence"
        else:
            prompt = f"請選出「{item['definition']}」的英文單字。"
            qtype = "meaning"

        questions.append({
            "word": item["word"],
            "definition": item["definition"],
            "example": item.get("example", ""),
            "prompt": prompt,
            "qtype": qtype,
            "choices": choices
        })

    return questions, signature

def refresh_all_question_sets():
    signature = get_bank_signature(st.session_state.word_bank)

    page2_questions, page2_signature = build_page2_questions(st.session_state.word_bank)
    page3_questions, page3_signature = build_page3_questions(st.session_state.word_bank)

    st.session_state.page2_questions = page2_questions
    st.session_state.page3_questions = page3_questions
    st.session_state.page2_signature = page2_signature
    st.session_state.page3_signature = page3_signature

    st.session_state.page2_submitted = False
    st.session_state.page3_submitted = False
    st.session_state.page2_score = 0
    st.session_state.page3_score = 0
    st.session_state.page2_wrong = []
    st.session_state.page3_wrong = []

def ensure_questions_ready():
    current_signature = get_bank_signature(st.session_state.word_bank)

    if st.session_state.page2_signature != current_signature:
        page2_questions, page2_signature = build_page2_questions(st.session_state.word_bank)
        st.session_state.page2_questions = page2_questions
        st.session_state.page2_signature = page2_signature
        st.session_state.page2_submitted = False
        st.session_state.page2_score = 0
        st.session_state.page2_wrong = []

    if st.session_state.page3_signature != current_signature:
        page3_questions, page3_signature = build_page3_questions(st.session_state.word_bank)
        st.session_state.page3_questions = page3_questions
        st.session_state.page3_signature = page3_signature
        st.session_state.page3_submitted = False
        st.session_state.page3_score = 0
        st.session_state.page3_wrong = []

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
        "🧠 第三頁：應用選英文",
        "📚 錯題本"
    ]
)

if st.sidebar.button("🗑️ 重設全部題庫"):
    st.session_state.word_bank = []
    refresh_all_question_sets()
    st.rerun()

# =========================================
# 5. 家長建立題庫
# =========================================
if page == "📝 家長建立題庫":
    st.title("📝 家長建立題庫")
    st.markdown(
        "<p class='normal-font'>不管你上傳什麼單字，都會自動帶入第一頁、第二頁、第三頁。</p>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs(["單筆輸入", "整批貼上", "PDF 匯入"])

    with tab1:
        with st.form("single_add_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                eng = st.text_input("英文單字")
            with col2:
                chi = st.text_input("中文意思")
            with col3:
                example = st.text_input("例句（可空白）")

            submitted = st.form_submit_button("➕ 加入題庫")
            if submitted:
                eng = normalize_word(eng)
                chi = clean_text(chi)
                example = clean_text(example)

                if eng and chi:
                    import_words([{
                        "word": eng,
                        "definition": chi,
                        "example": example
                    }])
                    st.success(f"已加入：{eng} / {chi}")
                else:
                    st.error("英文和中文都不能空白。")

    with tab2:
        st.markdown("<p class='normal-font'>請一行一筆。</p>", unsafe_allow_html=True)
        st.code(
            "accord,一致、符合,I accord with your idea.\n"
            "account,帳目、說明,We check the money in the account.\n"
            "most,最多的、大部分的\n"
            "least,最少的"
        )

        bulk_text = st.text_area("請貼上單字表", height=260)

        if st.button("📥 匯入整批單字"):
            parsed = parse_bulk_text(bulk_text)
            if parsed:
                import_words(parsed)
                st.success(f"成功匯入 {len(parsed)} 筆單字。")
            else:
                st.error("格式不正確。可用：英文,中文 或 英文,中文,例句")

    with tab3:
        st.markdown(
            "<p class='normal-font'>PDF 每行最好是：英文 中文 或 英文,中文,例句</p>",
            unsafe_allow_html=True
        )

        pdf_file = st.file_uploader("上傳 PDF 單字表", type=["pdf"], key="pdf_uploader")

        if pdf_file:
            try:
                extracted_text = load_words_from_pdf(pdf_file)
                st.text_area("📖 PDF 解析內容", extracted_text, height=260)

                if st.button("📥 將 PDF 內容轉成題庫"):
                    parsed = parse_bulk_text(extracted_text)
                    if parsed:
                        import_words(parsed)
                        st.success(f"成功匯入 {len(parsed)} 筆單字。")
                    else:
                        st.error("無法解析。請確認 PDF 每行格式清楚。")
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
        st.warning("⚠️ 題庫空空的，請先建立題庫。")
    else:
        st.markdown(
            "<p class='normal-font'>這一頁會自動使用你目前題庫的所有單字。</p>",
            unsafe_allow_html=True
        )

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
#    固定選項、固定 1/2/3/4、最後一次統一檢查
# =========================================
elif page == "🎯 第二頁：英文選中文":
    st.title("🎯 英文選中文")
    ensure_questions_ready()

    if len(st.session_state.word_bank) < 2:
        st.warning("⚠️ 至少要 2 個單字才能做選擇題。")
    else:
        st.markdown(
            "<p class='normal-font'>這一頁會使用你目前題庫的所有單字。選項固定 1、2、3、4，不會跳動。全部作答後再一次檢查答案。</p>",
            unsafe_allow_html=True
        )

        score = 0
        wrong_list = []

        for i, q in enumerate(st.session_state.page2_questions):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{q['word']}</p>",
                unsafe_allow_html=True
            )

            numbered_options = format_options_numbered(q["choices"])
            for opt in numbered_options:
                st.markdown(f"<div class='option-font'>{opt}</div>", unsafe_allow_html=True)

            selected_label = st.selectbox(
                "請選擇答案編號：",
                numbered_options,
                key=f"page2_select_{i}"
            )
            user_choice = extract_option_value(selected_label)

            if user_choice == q["definition"]:
                score += 1
            else:
                wrong_list.append({
                    "題號": i + 1,
                    "英文": q["word"],
                    "你的答案": user_choice,
                    "正確答案": q["definition"]
                })

        if st.button("📊 第二頁：檢查答案"):
            st.session_state.page2_score = score
            st.session_state.page2_wrong = wrong_list
            st.session_state.page2_submitted = True
            st.rerun()

        if st.session_state.page2_submitted:
            st.success(f"第二頁總分：{st.session_state.page2_score} / {len(st.session_state.page2_questions)}")

            if st.session_state.page2_wrong:
                st.subheader("❌ 第二頁錯題")
                st.dataframe(pd.DataFrame(st.session_state.page2_wrong), use_container_width=True)
            else:
                st.success("第二頁全部答對！")

# =========================================
# 8. 第三頁：應用選英文
#    一定帶入目前題庫所有單字
#    有例句就出例句填空，沒例句就出中文意思選英文
# =========================================
elif page == "🧠 第三頁：應用選英文":
    st.title("🧠 題庫總複習")
    ensure_questions_ready()

    if len(st.session_state.word_bank) < 2:
        st.warning("⚠️ 至少要 2 個單字才能做第三頁。")
    else:
        st.markdown(
            "<p class='normal-font'>這一頁也會使用你目前題庫的所有單字。有例句時出句子題；沒有例句時，改成中文意思選英文。全部作答後一次檢查答案。</p>",
            unsafe_allow_html=True
        )

        score = 0
        wrong_list = []

        for i, q in enumerate(st.session_state.page3_questions):
            st.markdown(
                f"<p class='big-font'>第 {i+1} 題：{q['prompt']}</p>",
                unsafe_allow_html=True
            )

            numbered_options = format_options_numbered(q["choices"])
            for opt in numbered_options:
                st.markdown(f"<div class='option-font'>{opt}</div>", unsafe_allow_html=True)

            selected_label = st.selectbox(
                "請選擇答案編號：",
                numbered_options,
                key=f"page3_select_{i}"
            )
            user_choice = extract_option_value(selected_label)

            if user_choice == q["word"]:
                score += 1
            else:
                wrong_list.append({
                    "題號": i + 1,
                    "題型": "句子題" if q["qtype"] == "sentence" else "中文題",
                    "題目": q["prompt"],
                    "你的答案": user_choice,
                    "正確答案": q["word"]
                })

        if st.button("📊 第三頁：檢查答案"):
            st.session_state.page3_score = score
            st.session_state.page3_wrong = wrong_list
            st.session_state.page3_submitted = True
            st.rerun()

        if st.session_state.page3_submitted:
            st.success(f"第三頁總分：{st.session_state.page3_score} / {len(st.session_state.page3_questions)}")

            if st.session_state.page3_wrong:
                st.subheader("❌ 第三頁錯題")
                st.dataframe(pd.DataFrame(st.session_state.page3_wrong), use_container_width=True)
            else:
                st.success("第三頁全部答對！")

# =========================================
# 9. 錯題本
# =========================================
elif page == "📚 錯題本":
    st.title("📚 錯題本")

    has_page2 = len(st.session_state.page2_wrong) > 0
    has_page3 = len(st.session_state.page3_wrong) > 0

    if not has_page2 and not has_page3:
        st.info("目前還沒有錯題紀錄。")
    else:
        if has_page2:
            st.subheader("第二頁錯題")
            df2 = pd.DataFrame(st.session_state.page2_wrong)
            st.dataframe(df2, use_container_width=True)

        if has_page3:
            st.subheader("第三頁錯題")
            df3 = pd.DataFrame(st.session_state.page3_wrong)
            st.dataframe(df3, use_container_width=True)
