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
    """
    從 Streamlit Secrets 中讀取 API_KEY_1 ~ API_KEY_5
    並隨機選出一組使用。
    """
    available_keys = []
    # 嘗試抓取 5 把鑰匙 + GOOGLE_API_KEY
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

# 初始化：選定本次操作預設要用的 Key
PROJECT_API_KEY = get_random_api_key()

# ==========================================

# 自訂 CSS
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    .metric-card { background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; color: #888; font-size: 12px; padding: 10px; background-color: #ffffff; pointer-events: none; border-top: 1px solid #eee; z-index: 100; }
    .block-container { padding-bottom: 80px; }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定與評分標準")
    
    # 1. API Key 狀態
    if PROJECT_API_KEY:
        st.success("✅ 系統已就緒 (多重金鑰保護中)")
    else:
        st.warning("⚠️ 未偵測到雲端 Key，請手動輸入")
        api_key_input = st.text_input("請輸入 Google API Key", type="password")
        PROJECT_API_KEY = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    
    # 2. 模型資訊
    st.subheader("🤖 AI 模型設定")
    target_model = "gemini-2.5-flash" 
    st.info("⚡ **AI 閱卷委員** (連線中)")
    st.caption("已鎖定指定模型版本。")
    
    st.markdown("---")
    
    # 3. 評分標準
    with st.expander("📚 大考中心評分標準 (細項)", expanded=True):
        st.markdown("""
        **內容 (Content)**
        - **5-4分 (優)**: 主題清楚切題，有具體、完整的相關細節支持。
        - **3分 (可)**: 主題不夠清楚或突顯，部分發展不全。
        - **2-1分 (差)**: 主題不明，大部分相關敘述發展不全或離題。
        
        **組織 (Organization)**
        - **5-4分 (優)**: 重點分明，有連貫性，轉承語使用得當。
        - **3分 (可)**: 重點安排不妥，前後發展比例與轉承語使用欠妥。
        - **2-1分 (差)**: 重點不明，前後不連貫。
        
        **文法句構 (Grammar)**
        - **5-4分 (優)**: 文法無錯誤，文句結構富變化。
        - **3分 (可)**: 文法、標點錯誤少，且不影響文意表達。
        - **2-1分 (差)**: 錯誤多，且明顯影響文意表達。
        
        **字彙拼字 (Vocabulary)**
        - **5-4分 (優)**: 用字精確、得宜，無拼字錯誤。
        - **3分 (可)**: 字詞單調、重複，偶有不當但無礙文意。
        - **2-1分 (差)**: 用字、拼字錯誤多，明顯影響文意。
        """)

st.title("💯英級棒!! 學測英文作文AI智慧批卷系統")
st.caption("專為學測英文科所打造，依大考中心數據校正的模擬閱卷系統。")

if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""
if 'essay_content' not in st.session_state:
    st.session_state.essay_content = ""

# --- 核心功能：強韌連線函數 (自動重試 + 故障轉移) ---
def call_gemini_api(prompt, key, model_name):
    # 準備所有可用的鑰匙清單 (從 secrets 讀取)
    keys_pool = []
    if "API_KEY_1" in st.secrets: keys_pool.append(st.secrets["API_KEY_1"])
    if "API_KEY_2" in st.secrets: keys_pool.append(st.secrets["API_KEY_2"])
    if "API_KEY_3" in st.secrets: keys_pool.append(st.secrets["API_KEY_3"])
    if "API_KEY_4" in st.secrets: keys_pool.append(st.secrets["API_KEY_4"])
    if "API_KEY_5" in st.secrets: keys_pool.append(st.secrets["API_KEY_5"])
    if "GOOGLE_API_KEY" in st.secrets: keys_pool.append(st.secrets["GOOGLE_API_KEY"])
    
    # 如果沒有設定 secrets，就用傳進來的單一 key
    if not keys_pool and key:
        keys_pool = [key]
    
    clean_model_name = model_name.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8} # 稍微提高創造力讓題目更多元
    }

    # 最多嘗試 3 次 (或是鑰匙池的數量，取大者)
    max_retries = max(3, len(keys_pool))
    
    for attempt in range(max_retries):
        # 輪流使用鑰匙 (Round Robin)
        current_key = keys_pool[attempt % len(keys_pool)]
        current_url = f"{url}?key={current_key}"
        
        try:
            response = requests.post(current_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    return result['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "⚠️ AI 回傳格式錯誤，請重試。"
            
            elif response.status_code == 429:
                st.toast(f"⚠️ 鑰匙 {attempt+1} 額度耗盡，正在切換備用鑰匙...", icon="🔄")
                time.sleep(2)
                continue
            
            else:
                return f"⚠️ 連線錯誤 (Status {response.status_code}): {response.text}"
                
        except Exception as e:
            return f"⚠️ 系統錯誤: {str(e)}"
            
    return "❌ 所有 API Key 額度皆已耗盡或連線失敗，請稍後再試。"

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
                with st.spinner("AI 閱卷委員正在隨機設計多元題目..."):
                    # 🔥 題目 Prompt：強制全中文 + 多元主題 🔥
                    prompt_gen = """
                    角色：你是一位創意豐富的台灣高中英文學測出題老師。
                    任務：請「隨機」從以下類別中挑選一個，設計一個符合台灣高中生生活經驗的英文作文題目。
                    
                    類別池：
                    1. **食衣住行育樂** (夜市、捷運、網購、旅遊)
                    2. **台灣特色** (便利商店、傳統節慶、手搖飲)
                    3. **校園生活** (社團、考試、人際關係)
                    4. **社會觀察** (博愛座、AI影響、環保)
                    5. **自我成長** (面對失敗、夢想、時間管理)

                    ⚠️ **嚴格規範 (Strict Rules)**:
                    1. **所有說明文字必須是「繁體中文」**。
                    2. 絕對不要出現 "In your first paragraph..." 這種英文指令。
                    3. 請模仿大考中心的出題語氣。

                    輸出格式範本：
                    --------------------------------
                    **題目說明**：
                    [這裡放約 50-80 字的題目引言，全中文]

                    **寫作引導**：
                    第一段請說明...[全中文說明]
                    第二段請描述...[全中文說明]
                    --------------------------------
                    """
                    current_key = get_random_api_key() or PROJECT_API_KEY
                    result = call_gemini_api(prompt_gen, current_key, target_model)
                    st.session_state.generated_topic = result
        
        if st.session_state.generated_topic:
            st.info("👇 模擬試題：")
            st.markdown(st.session_state.generated_topic)
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
            # 🔥 批改 Prompt：強化學習回饋版 (Level 5-6 單字庫 + 詳細解析) 🔥
            system_prompt = f"""
            # Role: 台灣學測英文作文資深閱卷委員 (Senior Grader)
            
            # Context:
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # 📊 113年學測評分常模 (Norm-Referenced Grading):
            請依照以下「考生累計百分比」來決定分數落點。
            1. **【18-20 分 (神級)】**: 全台前 0.6%。思想深刻、修辭優美、幾乎無懈可擊。
            2. **【15-17 分 (頂標)】**: 全台前 7.8%。內容豐富、組織嚴謹。允許極少數微小瑕疵。
            3. **【12-14 分 (前標)】**: 全台前 27%。結構完整，論點清楚。可能有少許文法錯誤。
            4. **【8-11 分 (均標)】**: 中段 50%。能溝通，但句型單調或有明顯文法錯誤。

            # Task: 產出結構化的 Markdown 批改報告
            
            ## Part 1: 總分與點評
            請給出總分 (0-20)，並用一句話描述這篇文章在全體考生中的「落點位置」。
            
            ## Part 2: 四大構面評分 (0-5分)
            - 內容: [分數] (簡評)
            - 組織: [分數] (簡評)
            - 文法: [分數] (簡評)
            - 字彙: [分數] (簡評)
            
            ## Part 3: 逐句訂正 (Visual Correction)
            請找出文中 3-5 個最需要改進的句子。
            **⚠️ 排版要求：請使用 Markdown 列表符號「-」開頭，確保換行。**
            
            格式範例：
            > ### 🚩 改進點 1
            > - 🔴 **原句**: :red[He go to school.]
            > - 🟢 **訂正**: :green[He **went** to school.]
            > - 💡 **解析**: 這裡發生了時態錯誤... (請用繁體中文詳細解釋文法規則，讓學生能學到東西)
            
            ## Part 4: 升級與加分 (Advanced Vocabulary & Phrasing)
            **請提供 3 個 Level 5-6 (指考/托福等級) 的高級詞彙替換建議，需包含詞性與解釋。**
            
            格式範例：
            > ### 🌟 升級建議 1
            > - 🔹 **原文**: :blue[very good]
            > - 🚀 **升級**: **impeccable** (adj. 無懈可擊的)
            > - 📝 **解析**: "very good" 太過平淡。**Impeccable** 強調完美無缺，適合用來形容表現或品質，能展現更高級的程度副詞運用。
            
            > ### 🌟 升級建議 2
            > - 🔹 **原文**: ...
            > - 🚀 **升級**: ...
            > - 📝 **解析**: ...
            
            > ### ✍️ 實用加分句型
            > - (提供一個與文章主題相關的高級句型或諺語，並解釋用法)
            """
            
            with st.spinner("AI 閱卷委員正在嚴格閱卷中..."):
                current_key = get_random_api_key() or PROJECT_API_KEY
                result = call_gemini_api(system_prompt, current_key, target_model)
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.success("🎉 閱卷完成！")
                    st.markdown(result)
                    st.divider()
                    st.caption("📢 本批改結果僅供學習參考。")

st.markdown("---")
st.markdown("<div class='footer'>製作者：中央大學資管系二年級 蔡仁懋</div>", unsafe_allow_html=True)