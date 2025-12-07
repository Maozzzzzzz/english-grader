import streamlit as st
import requests
import json
import re
import random
import time

# 頁面設定
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI智慧批卷系統", 
    page_icon="💯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 多重金鑰負載平衡系統
# ==========================================
def get_random_api_key():
    available_keys = []
    if "API_KEY_1" in st.secrets: available_keys.append(st.secrets["API_KEY_1"])
    if "API_KEY_2" in st.secrets: available_keys.append(st.secrets["API_KEY_2"])
    if "API_KEY_3" in st.secrets: available_keys.append(st.secrets["API_KEY_3"])
    if "API_KEY_4" in st.secrets: available_keys.append(st.secrets["API_KEY_4"])
    if "API_KEY_5" in st.secrets: available_keys.append(st.secrets["API_KEY_5"])
    if "GOOGLE_API_KEY" in st.secrets: available_keys.append(st.secrets["GOOGLE_API_KEY"])
    
    if available_keys:
        return random.choice(available_keys)
    else:
        return None

PROJECT_API_KEY = get_random_api_key()

# ==========================================
# CSS 優化 (完全自適應淺色/深色模式)
# ==========================================
st.markdown("""
<style>
    /* 修正輸入框字體大小 */
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    
    /* 修正指標卡片 (Metric Card) 
       使用 var(--secondary-background-color) 讓它自動適應：
       - 深色模式時：它是深灰色
       - 淺色模式時：它是淺灰色
    */
    .metric-card { 
        background-color: var(--secondary-background-color); 
        border-radius: 10px; 
        padding: 15px; 
        text-align: center; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); 
    }
    
    /* 頁尾固定 
       使用 var(--background-color) 確保背景色跟隨主題
    */
    .footer { 
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%; 
        text-align: center; 
        color: var(--text-color); /* 自動變色 */
        font-size: 12px; 
        padding: 10px; 
        background-color: var(--background-color); 
        pointer-events: none; 
        border-top: 1px solid rgba(49, 51, 63, 0.2); 
        z-index: 100; 
    }
    .block-container { padding-bottom: 80px; }
    
    /* 🔥 關鍵修正：使用 var(--text-color) 取代 #ffffff 
       這會讓標題在深色模式變白，在淺色模式變黑
    */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color) !important;
        font-weight: 600 !important;
    }
    
    /* 修正 Markdown 內文顏色 */
    p, li, span, div {
        color: var(--text-color) !important;
        font-size: 16px !important;
    }
    
    /* 修正 Streamlit Widget Label */
    .stRadio label, .stTextInput label, .stTextArea label, .stSelectbox label {
        color: var(--text-color) !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }

    /* Tab 標籤顏色自動適應 */
    .stTabs [data-baseweb="tab"] {
        color: var(--text-color);
    }
    
    /* 優化 Metric 數值顏色 (保持紅色醒目，但在淺色模式也好讀) */
    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        color: #ff4b4b !important; 
    }
    [data-testid="stMetricLabel"] {
        font-size: 16px !important;
        color: var(--text-color) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄 ---
with st.sidebar:
    st.title("⚙️ 設定與評分標準")
    if PROJECT_API_KEY:
        st.success("✅ 系統已就緒 (多重金鑰保護中)")
    else:
        st.warning("⚠️ 未偵測到雲端 Key，請手動輸入")
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        PROJECT_API_KEY = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    st.subheader("🤖 AI 模型設定")
    target_model = "gemini-2.5-flash" 
    st.info("⚡ **AI 閱卷委員** (連線中)")
    st.caption("已鎖定指定模型版本。")
    
    st.markdown("---")
    with st.expander("📚 大考中心評分標準 (細項)", expanded=True):
        st.markdown("""
        **內容 (Content)**
        - **5-4分**: 主題清楚切題，細節支持完整。
        - **3分**: 主題不夠突顯。
        - **2-1分**: 離題。
        
        **組織 (Organization)**
        - **5-4分**: 連貫性佳。
        - **3分**: 轉折生硬。
        - **2-1分**: 支離破碎。
        
        **文法 & 字彙**
        - **5-4分**: 精確，無明顯錯誤。
        - **3分**: 錯誤少，不影響文意。
        - **2-1分**: 錯誤多，影響閱讀。
        """)

st.title("💯英級棒!! 學測英文作文AI智慧批卷系統")
st.caption("專為學測英文科所打造，依大考中心數據校正的模擬閱卷系統。")

if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""
if 'essay_content' not in st.session_state:
    st.session_state.essay_content = ""

# --- 核心連線函數 ---
def call_gemini_api(prompt, key, model_name):
    keys_pool = []
    if "API_KEY_1" in st.secrets: keys_pool.append(st.secrets["API_KEY_1"])
    if "API_KEY_2" in st.secrets: keys_pool.append(st.secrets["API_KEY_2"])
    if "API_KEY_3" in st.secrets: keys_pool.append(st.secrets["API_KEY_3"])
    if "API_KEY_4" in st.secrets: keys_pool.append(st.secrets["API_KEY_4"])
    if "API_KEY_5" in st.secrets: keys_pool.append(st.secrets["API_KEY_5"])
    if "GOOGLE_API_KEY" in st.secrets: keys_pool.append(st.secrets["GOOGLE_API_KEY"])
    
    if not keys_pool and key: keys_pool = [key]
    
    clean_model_name = model_name.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }

    max_retries = max(3, len(keys_pool))
    
    for attempt in range(max_retries):
        current_key = keys_pool[attempt % len(keys_pool)]
        current_url = f"{url}?key={current_key}"
        try:
            response = requests.post(current_url, headers=headers, json=data)
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except: return "⚠️ AI 回傳格式錯誤，請重試。"
            elif response.status_code == 429:
                st.toast(f"⚠️ 線路 {attempt+1} 忙碌，切換中...", icon="🔄")
                time.sleep(1.5)
                continue
            else:
                return f"⚠️ 連線錯誤: {response.status_code}"
        except Exception as e:
            return f"⚠️ 系統錯誤: {str(e)}"
    return "❌ 系統忙碌中，請稍後再試。"

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改區"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("📍 設定題目")
    col1, col2 = st.columns([1, 2])
    with col1:
        topic_source = st.radio("題目來源：", ["AI 自動出題", "自行輸入"])
    
    current_topic = ""
    
    if topic_source == "AI 自動出題":
        if st.button("✨ 生成模擬試題 (隨機)", type="primary"):
            if not PROJECT_API_KEY:
                st.error("❌ 請先設定 API Key")
            else:
                with st.spinner("AI 閱卷委員正在出題..."):
                    prompt_gen = """
                    角色：大考中心出題委員。
                    任務：隨機設計一個學測英文作文題目 (食/衣/住/行/文化/校園/時事/成長)，題目越多元、生活化越好。
                    
                    ⚠️ **Strict Output Rules (嚴格輸出規範)**:
                    1. **禁止** 任何開場白。
                    2. **禁止** 出現英文指令。
                    3. 標題與內文格式必須統一。
                    
                    請直接輸出以下內容 (全繁體中文)：
                    
                    ### 題目：[請在此填入題目名稱]
                    
                    **引文說明**：
                    [50-80字的引導文字，語氣要正式]
                    
                    **第一段引導**：
                    在此說明第一段應該包含的內容重點。
                    
                    **第二段引導**：
                    在此說明第二段應該包含的內容重點。
                    """
                    current_key = get_random_api_key() or PROJECT_API_KEY
                    result = call_gemini_api(prompt_gen, current_key, target_model)
                    st.session_state.generated_topic = result
        
        if st.session_state.generated_topic:
            st.markdown(st.session_state.generated_topic)
            st.info("💡 **小提醒：學測英文作文建議作答字數為 120 字以上 (約 150-180 字為佳)，請盡量發揮！**")
            current_topic = st.session_state.generated_topic
    else:
        current_topic = st.text_area("請輸入題目說明", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("📍 寫作與批改")
    
    if current_topic:
        with st.expander("📄 點擊查看當前題目", expanded=False):
            st.markdown(current_topic)
    else:
        st.warning("⚠️ 尚未設定題目")

    user_essay = st.text_area("請在此輸入英文作文：", value=st.session_state.essay_content, height=300, key="essay_input")
    
    word_count = len(re.findall(r'\w+', user_essay))
    if word_count > 0:
        st.caption(f"📊 目前字數：{word_count} 字")

    if st.button("🚀 開始批改", type="primary", use_container_width=True):
        if not PROJECT_API_KEY:
            st.error("❌ 請先設定 API Key！")
        elif not user_essay:
            st.warning("⚠️ 請輸入作文內容！")
        else:
            system_prompt = f"""
            # Role: 台灣學測英文作文「地獄級」閱卷委員 (Hell-mode Grader)
            
            # Context:
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # ⚠️ 評分邏輯 (Strict Scoring Protocol):
            **基準分：10分(大部分高中生的起點)**
            
            **1. 分數天花板 (Score Ceiling) - 必須嚴格執行**:
            - ❌ **上限 11 分**: 如果文章用字僅限於國中程度 (good, bad, happy, think) 且缺乏句型變化。
            - ❌ **上限 14 分**: 如果文章通順，但出現許多明顯文法錯誤 (時態、單複數)。
            - ✅ **15 分以上**: 必須同時滿足「思想有深度」+「用字精準 (Level 5-6)」+「僅有些許文法錯誤」。
            
            **2. 常模分佈**:
            - 15-20分: 前 7% (極稀有，不要輕易給)。
            - 12-14分: 前 27% (頂標/前標)。
            - 9-11分: 中段班 (大多數落點)。
            - 8分以下: 基礎不穩。

            # Task: 產出結構化的 Markdown 批改報告
            
            ## Part 1: 總分與犀利點評
            總分 (0-20)：[分數]
            一句話點評：(請用嚴格的角度，直接點出缺點，例如：「雖然結構完整，但用字過於淺顯，像國中生作文，無法拿到高分。」)
            
            ## Part 2: 四大構面評分 (0-5分)
            - 內容: [分數] 
            - 組織: [分數] 
            - 文法: [分數] 
            - 字彙: [分數] 
            
            ## Part 3: 逐句訂正 (Visual Correction)
            **請找出 3-5 個錯誤，解析必須詳細 (超過 30 字)，解釋為什麼錯。**
            (請嚴格使用 Markdown 列表符號「-」確保換行)
            
            > ### 🚩 改進點 1
            > - 🔴 **原句**: :red[...]
            > - 🟢 **訂正**: :green[...]
            > - 💡 **解析**: ...
            
            ## Part 4: Level 5-6 高級字彙升級 (Vocabulary Upgrade)
            **請提供 3-5 個高級單字建議，必須包含「詞性」、「中文」、「等級」與「詳細用法」。**
            
            > ### 🌟 升級建議 1
            > - 🔹 **原文**: :blue[...]
            > - 🚀 **升級**: **[高級單字]** ([詞性], [中文意思]) (Level [5或6])
            > - 📝 **解析**: ...
            
            ## Part 5: 實用加分句型 (Bonus Sentence Patterns)
            **請提供 3 組「截然不同類型」的高級句型 (例如：一組倒裝句、一組分詞構句、一組虛擬語氣)，不要重複類似結構。**
            
            > ### ✍️ 句型 1：[句型名稱，如：倒裝句]
            > - **句型結構**: [結構說明]
            > - **範例**: [造句]
            > - **如何套用**: [說明如何改寫本文中的句子]
            
            > ### ✍️ 句型 2：[句型名稱，如：分詞構句]
            > - ...
            
            > ### ✍️ 句型 3：[句型名稱]
            > - ...
            """
            
            with st.spinner("AI 閱卷委員正在嚴格審視中..."):
                current_key = get_random_api_key() or PROJECT_API_KEY
                result = call_gemini_api(system_prompt, current_key, target_model)
                
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.success("🎉 閱卷完成！")
                    
                    try:
                        # 使用 Regex 抓取分數
                        total_match = re.search(r"總分.*?[:：]\s*(\d+)", result)
                        content_match = re.search(r"內容.*?[:：]\s*(\d+)", result)
                        org_match = re.search(r"組織.*?[:：]\s*(\d+)", result)
                        gram_match = re.search(r"文法.*?[:：]\s*(\d+)", result)
                        vocab_match = re.search(r"字彙.*?[:：]\s*(\d+)", result)
                        
                        total_score = total_match.group(1) if total_match else "N/A"
                        s_content = content_match.group(1) if content_match else "0"
                        s_org = org_match.group(1) if org_match else "0"
                        s_gram = gram_match.group(1) if gram_match else "0"
                        s_vocab = vocab_match.group(1) if vocab_match else "0"
                        
                        st.subheader("📊 評分摘要")
                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric("🏆 總分", f"{total_score} / 20")
                        c2.metric("📝 內容", f"{s_content} / 5")
                        c3.metric("🏗️ 組織", f"{s_org} / 5")
                        c4.metric("⚖️ 文法", f"{s_gram} / 5")
                        c5.metric("🔤 字彙", f"{s_vocab} / 5")
                        st.divider()
                        
                    except Exception as e:
                        pass
                    
                    st.markdown(result)
                    st.divider()
                    st.caption("📢 本結果依大考中心配分標準所批改，若有疑問請洽詢製作者。")

st.markdown("---")
st.markdown("<div class='footer'>製作者：中央大學資管系二年級 蔡仁懋 m20060719@gmail.com </div>", unsafe_allow_html=True)