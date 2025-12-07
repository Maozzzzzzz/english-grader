import streamlit as st
import requests
import json
import re
import random
import google.generativeai as genai

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
    從 Streamlit Secrets 中讀取 API_KEY_1, API_KEY_2, API_KEY_3
    並隨機選出一組使用。
    """
    available_keys = []
    # 嘗試抓取 3 把鑰匙
    if "API_KEY_1" in st.secrets: available_keys.append(st.secrets["API_KEY_1"])
    if "API_KEY_2" in st.secrets: available_keys.append(st.secrets["API_KEY_2"])
    if "API_KEY_3" in st.secrets: available_keys.append(st.secrets["API_KEY_3"])
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
    
    # 2. 模型資訊 (🔥 依照指示強制鎖定 2.5-flash 🔥)
    st.subheader("🤖 AI 模型設定")
    target_model = "gemini-2.5-flash" 
    st.info(f"⚡ 目前固定使用：\n**{target_model}**")
    st.caption("已鎖定指定模型版本。")
    
    st.markdown("---")
    
    # 3. 評分標準 (已更新為詳細文字說明)
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

# --- 核心功能：萬能連線函數 ---
def call_gemini_api(prompt, key, model_name):
    clean_model_name = model_name.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9} # 提高創意度
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "⚠️ AI 回傳格式錯誤，請重試。"
        else:
            return f"⚠️ 連線錯誤 (Status {response.status_code}): {response.text}"
    except Exception as e:
        return f"⚠️ 系統錯誤: {str(e)}"

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
                with st.spinner(f"AI ({target_model}) 正在隨機設計多元題目..."):
                    # 🔥 題目 Prompt：加入多元主題 (食衣住行、台灣特色等) 🔥
                    prompt_gen = """
                    角色：你是一位創意豐富的高中英文學測出題老師。
                    任務：請「隨機」從以下類別中挑選一個，設計一個符合台灣高中生生活經驗的英文作文題目：
                    1. **食衣住行育樂** (例如：夜市小吃、捷運文化、網購經驗、國內旅遊)
                    2. **台灣特色** (例如：便利商店的便利性、傳統節慶如中秋烤肉、手搖飲文化)
                    3. **校園生活與人際** (例如：社團活動、考試壓力、與同學的衝突、好朋友的特質)
                    4. **時事與社會觀察** (例如：博愛座爭議、外送平台興起、氣候變遷的感受)
                    5. **親情與家庭** (例如：與長輩的代溝、一次難忘的家庭聚餐、做家事的體悟)
                    6. **自我成長** (例如：如何面對失敗、學會獨處、未來的夢想)

                    請確保題目多樣化，且引導明確讓學生知道寫作重點
                    
                    輸出格式要求：
                    1. 不需顯示你選了哪個類別。
                    2. 題目引文 (約 50-80 字，全中文，模擬考卷語氣)。
                    3. 第一段引導 (說明應包含的內容)。
                    4. 第二段引導 (說明應包含的內容)。
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

    # (Demo 按鈕已移除)

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
            # 🔥 批改 Prompt：參考側邊欄標準 🔥
            system_prompt = f"""
            # Role: 台灣學測英文作文閱卷委員 (Strict Grader)
            # Context:
            【題目】{current_topic}
            【學生作文】{user_essay}
            
            # 評分標準 (依照大考中心規範):
            1. **內容 (0-5)**: 主題是否切題？細節是否支持論點？
            2. **組織 (0-5)**: 結構是否連貫？轉承語使用是否恰當？
            3. **文法 (0-5)**: 句構變化與正確性。
            4. **字彙 (0-5)**: 用字精確度與拼字。

            # Objective: 根據 113 年大考中心真實統計數據進行評分，絕對避免分數通膨。
            你必須嚴格遵守以下分數分佈常模，不可給予虛高的鼓勵分：
            
            1. **【神級範文】19 ~ 20 分 (Top 0.16%)**
               - 統計事實：全台灣僅不到 0.2% 考生達到此區間。
               - 評分標準：思想極具深度、語言如母語人士般精準、修辭優美，完全無語法錯誤。
               - *除非文章完美無瑕，否則不給此高分。*

            2. **【頂標高手】15 ~ 18 分 (Top 7.8%)**
               - 統計事實：15分以上僅佔全體前 7.8%。
               - 評分標準：內容豐富、組織嚴謹、句型變化多樣。允許極少量的微小錯誤，但不影響閱讀流暢度。
            
            3. **【前標佳作】12 ~ 14 分 (Top 27%)**
               - 統計事實：約落在前 8% ~ 27% 區間。
               - 評分標準：結構完整，能清楚表達論點。有些許文法或用字錯誤，但大體通順。
            
            4. **【均標中等】8 ~ 11 分 (Top 28% ~ 56%)**
               - 統計事實：這是最龐大的中段班。
               - 評分標準：能大致表達意思，但內容較為單薄，或文法、拼字錯誤較多，影響閱讀體驗。
            
            5. **【待加強】0 ~ 7 分 (Bottom 43%)**
               - 統計事實：約 43% 的考生在此區間 (包含 10% 的 0 分)。
               - 評分標準：離題、字數嚴重不足、語意不清、中式英文嚴重，或無法完整成句。

            # Task:
            請產出一份 Markdown 格式的批改報告，包含：
            1. **總分與簡評**: 給予一個總分 (0-20)，並用一句話總結。
            2. **分項評分**: 針對上述四項給分並簡述原因。
            3. **逐句訂正**: 請列出 3-5 個主要錯誤，格式為「🔴原句 -> 🟢訂正 -> 💡解析」，要多善用標記或不同字，讓使用者可以更容易抓到訂正重點。
            4. **升級建議**: 提供 3 個可以替換的高級單字或片語。
            """
            
            with st.spinner(f"AI ({target_model}) 正在嚴格閱卷中..."):
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