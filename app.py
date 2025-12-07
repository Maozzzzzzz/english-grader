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
# CSS 優化 (修復深色模式字體看不見的問題)
# ==========================================
st.markdown("""
<style>
    /* 修正輸入框字體大小 */
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    
    /* 修正指標卡片 */
    .metric-card { background-color: #262730; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); }
    
    /* 頁尾固定 */
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; color: #888; font-size: 12px; padding: 10px; background-color: #0e1117; pointer-events: none; border-top: 1px solid #333; z-index: 100; }
    .block-container { padding-bottom: 80px; }
    
    /* 🔥 關鍵修正：將所有標題強制設為白色，確保深色模式可讀 🔥 */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* 修正 Markdown 內文顏色，避免被蓋掉 */
    p, li, span {
        color: #e0e0e0 !important;
        font-size: 16px !important;
    }
    
    /* 特別針對 Streamlit 的 Tab 標籤顏色 */
    .stTabs [data-baseweb="tab"] {
        color: #ffffff;
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
        "generationConfig": {"temperature": 0.4} # 🔥 溫度降到 0.4，讓評分更冷靜客觀
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
                    任務：隨機設計一個學測英文作文題目 (食衣住行/文化/校園/時事/成長)。
                    
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
            # 🔥 批改 Prompt：殘酷評分 + 字體白化 + 句型擴充版 🔥
            system_prompt = f"""
            # Role: 台灣學測英文作文「殘酷」閱卷委員 (Ruthless Grader)
            
            # Context:
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # ⚠️ 評分邏輯修正：起點錨定法 (Anchor Pricing)
            **請預設這篇文章只有 10 分 (均標)。**
            除非你能找到「極具說服力」的證據證明它值得更高分，否則不要加分。
            
            1. **【15-20 分 (神級)】**: 
               - **條件**: 幾乎無懈可擊。用字如 native speaker 般精準，句型變化多端。
               - **現實**: 只有不到 7% 的人能拿到。**若有任何明顯文法錯，絕不給此區間。**
            
            2. **【12-14 分 (前標)】**:
               - **條件**: 結構完整，論點清楚。
               - **現實**: 這是「好學生」的天花板。普通的通順文章頂多 12 分。
            
            3. **【8-11 分 (均標)】**:
               - **條件**: 能溝通，但用字平淡 (good, bad, happy)，或有中式英文。
               - **現實**: **這是大多數高中生的落點。請勇敢給出 10 分或 11 分。**

            # Task: 產出結構化的 Markdown 批改報告
            
            ## Part 1: 總分與犀利點評
            總分 (0-20)：[分數]
            一句話點評：(請用嚴格的角度，直接點出這篇文章為什麼拿不到更高分，例如：「雖然通順，但用字過於國中程度，無法進入前標。」)
            
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
            **請提供 3 組不同類型的高級句型，幫助學生提升文章層次。**
            
            > ### ✍️ 句型 1：[句型名稱，如：倒裝句]
            > - **句型結構**: [結構說明]
            > - **範例**: [造句]
            > - **如何套用**: [說明如何用在本文]
            
            > ### ✍️ 句型 2：[句型名稱，如：分詞構句]
            > - ...
            
            > ### ✍️ 句型 3：[句型名稱，如：假設語氣]
            > - ...
            """
            
            with st.spinner("AI 閱卷委員正在嚴格審視中 (預設分數：10分)..."):
                current_key = get_random_api_key() or PROJECT_API_KEY
                result = call_gemini_api(system_prompt, current_key, target_model)
                
                if "⚠️" in result:
                    st.error(result)
                else:
                    st.success("🎉 閱卷完成！")
                    st.markdown(result)
                    st.divider()
                    st.caption("📢 本結果依大考中心配分標準所批改，若有疑問請洽詢製作者。")

st.markdown("---")
st.markdown("<div class='footer'>製作者：中央大學資管系二年級 蔡仁懋 m20060719@gmail.com </div>", unsafe_allow_html=True)