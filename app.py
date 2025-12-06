import streamlit as st
import requests
import json

# 頁面設定
st.set_page_config(
    page_title="英級棒!! 學測英文作文AI批改APP", 
    page_icon="💯", 
    layout="wide"
)

# --- 側邊欄設計 ---
with st.sidebar:
    st.title("⚙️ 設定")
    # API Key 輸入
    api_key_input = st.text_input("請輸入 Google API Key", type="password", help="請前往 Google AI Studio 免費申請")
    api_key = api_key_input.strip() if api_key_input else ""
    
    st.markdown("---")
    
    # 🔥🔥🔥 API 健檢工具 🔥🔥🔥
    st.subheader("🔍 API 健檢")
    if st.button("檢測我的 API Key"):
        if not api_key:
            st.error("請先輸入 API Key！")
        else:
            try:
                # 直接問 Google：這把鑰匙能用哪些模型？
                check_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                resp = requests.get(check_url)
                
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
                    st.success(f"✅ 驗證成功！你的帳號支援 {len(models)} 個模型。")
                    st.code(models)
                else:
                    st.error(f"❌ 檢測失敗 (代碼 {resp.status_code}): {resp.text}")
            except Exception as e:
                st.error(f"檢測時發生錯誤: {e}")

    st.markdown("---")
    
    st.subheader("🤖 AI 模型選擇")
    # 這裡更新為你帳號實際擁有的模型列表
    # 我將最新的 2.5 和 2.0 系列放在最前面
    user_available_models = [
        'gemini-2.5-flash', 
        'gemini-2.5-pro', 
        'gemini-2.0-flash', 
        'gemini-2.0-flash-lite',
        'gemini-2.0-pro-exp-02-05',
        'gemini-flash-latest', 
        'gemini-pro-latest',
        'gemini-1.5-flash',
        'gemini-1.5-pro'
    ]
    
    model_option = st.selectbox(
        "請選擇模型：",
        user_available_models,
        index=0, # 預設選第一個 (gemini-2.5-flash)
        help="這些是你帳號目前可用的最新模型，建議使用 2.5 或 2.0 系列。"
    )
    
    st.markdown("---")
    st.subheader("📚 官方評量重點")
    st.info("""
    **核心原則 (由重到輕)：**
    1. **溝通有效性**：是否清楚傳達想法？
    2. **正確與自然**：語法是否正確？
    3. **詞彙與句構**：是否精準運用高中詞彙？
    4. **文體與創意**：修辭是否優美？
    
    *依據高中英語文參考詞彙表 (約 6000 字) 為基準。*
    """)

st.title("💯 英級棒!! 學測英文作文 AI 批改 APP")
st.markdown("### 專為台灣高中生打造，你的 24 小時專屬英文家教！")

# 初始化 Session State
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""

# --- 核心功能：萬能連線函數 ---
def call_gemini_api(prompt, key, model_name):
    # 建構 URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    
    headers = {'Content-Type': 'application/json'}
    # 設定參數 (降低隨機性，讓評分穩定)
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "⚠️ 發生錯誤：AI 回傳了怪怪的格式，請再試一次。"
        else:
            return f"⚠️ 連線錯誤 (Status {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"⚠️ 系統錯誤：{str(e)}"

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("📍 步驟一：設定題目")
    topic_source = st.radio("請選擇題目來源：", ["自行上傳/輸入題目", "請 AI 幫我出題 (食衣住行育樂)"])
    
    current_topic = ""
    
    if topic_source == "請 AI 幫我出題 (食衣住行育樂)":
        if st.button("✨ 立即生成模擬試題"):
            if not api_key:
                st.error("❌ 請先在左側輸入 Google API Key！")
            else:
                with st.spinner(f"正在使用 {model_option} 模型出題中..."):
                    prompt_gen = """
                    你現在是台灣高中英文學測的出題老師。請從「食、衣、住、行、育、樂」中隨機選一個主題，
                    設計一個符合學測格式的英文作文題目。
                    格式要求：
                    1. 題目提示：一段約 50 字的繁體中文背景描述，貼近台灣學生生活。
                    2. 清楚列出「第一段」與「第二段」必須涵蓋的內容。
                    請直接輸出題目內容即可，不要有多餘的開場白。
                    """
                    result = call_gemini_api(prompt_gen, api_key, model_option)
                    
                    if "⚠️" in result:
                        st.error(result)
                        st.warning("👉 請在左側切換其他模型試試看！")
                    else:
                        st.session_state.generated_topic = result
        
        if st.session_state.generated_topic:
            st.success("出題完成！")
            st.markdown(st.session_state.generated_topic)
            current_topic = st.session_state.generated_topic

    else:
        current_topic = st.text_area("請輸入題目說明", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("📍 步驟二：輸入作文並批改")
    
    user_essay = st.text_area("請在此輸入你的英文作文 (建議至少 120 字)", height=300)
    
    if st.button("🚀 英級棒批改開始！"):
        if not api_key:
            st.error("❌ 請先在左側輸入 API Key！")
        elif not user_essay:
            st.warning("⚠️ 請輸入作文內容！")
        else:
            # 這裡更新了 System Prompt，加入官方評分邏輯與 6000 單標準
            system_prompt = f"""
            你是一位台灣頂尖的高中英文補習班名師，同時也是熟悉大考中心閱卷標準的資深閱卷老師。
            你的目標是幫學生在學測拿到 15 級分以上的高標。

            【題目資訊】
            {current_topic}
            
            【學生作文】
            {user_essay}
            
            【評量依據與核心原則】
            1. **評量重點**：運用高中參考詞彙表 (約 6000 單) 之詞彙與語法，寫出切合主題、具一致性與連貫性的短文。
            2. **評分優先順序 (由重到輕)**：
               (1) **溝通有效性**：是否清楚傳達想法？(內容發展完整、切題)
               (2) **語言正確與自然度**：語法錯誤是否影響理解？
               (3) **詞彙層級與句構變化**：是否精準使用高中詞彙？(難字誤用扣分，正確使用加分)
               (4) **文體優美與創意表達**

            【評分任務：四大構面 (各 0-5 分，滿分 20)】
            請嚴格依據五級分制評分：
            
            1. **內容 (Content)**
               - 5-4分：主題清楚，有具體細節支持，發展完整。
               - 3分：主題尚可，部分發展不全。
               - 2-1分：離題或內容貧乏。
            2. **組織 (Organization)**
               - 5-4分：結構(開頭/發展/結尾)清楚，轉折詞(Transitions)使用自然，語意連貫。
               - 3分：連貫性略弱。
               - 2-1分：句子鬆散或跳躍。
            3. **文法句構 (Grammar)**
               - 5-4分：句型多樣，錯誤極少且不影響理解。
               - 3分：有些錯誤但文意清楚。
               - 2-1分：錯誤頻繁影響理解。
            4. **字彙拼字 (Vocabulary)**
               - 5-4分：用字精準自然，詞彙運用得體。
               - 3分：用字單調或重複。
               - 2-1分：詞性錯誤或拼字頻繁錯誤。
            
            **分數控制**：中位數約 12 分，15 分以上為高標。

            【輸出格式 (Markdown)】
            請務必按照以下格式輸出：
            
            ## 📊 綜合評分: [總分]/20
            - **內容**: [分數]/5
            - **組織**: [分數]/5
            - **文法**: [分數]/5
            - **字彙**: [分數]/5

            ## 📝 名師總評
            (約 100 字，請以閱卷老師的角度，先評論「溝通有效性」與「結構」，再評論「語言正確性」。語氣專業、鼓勵但嚴格。)

            ## 🔍 手術式批改 (重點改進)
            (請挑出 3 個最具代表性的錯誤，針對「詞彙誤用」、「中式英文」或「句構鬆散」進行修正)
            **1. [分類]**
            > **原文**: "..."
            > **❌ 問題**: ...
            > **✅ 名師升級**: "..."
            > **💡 解析**: ...
            (重複 3 次)

            ## 🚀 下一步練習建議
            (針對學生的弱點，給出一個具體建議，例如：「多練習轉折詞的使用」、「加強 4500-6000 單的搭配詞運用」)
            """

            with st.spinner(f"AI 名師 ({model_option}) 正在依據大考中心標準閱卷中..."):
                result = call_gemini_api(system_prompt, api_key, model_option)
                
                if "⚠️" in result:
                    st.error(result)
                    st.warning("👉 請嘗試在左側切換其他模型！")
                else:
                    st.markdown(result)