import streamlit as st
from openai import OpenAI

# 頁面設定
st.set_page_config(page_title="學測英文作文AI批改名師", page_icon="📝", layout="wide")

# 側邊欄：設定與說明
with st.sidebar:
    st.title("⚙️ 設定")
    api_key = st.text_input("請輸入 OpenAI API Key", type="password", help="請前往 OpenAI 官網申請 API Key")
    
    st.markdown("---")
    st.subheader("關於評分標準")
    st.info("""
    本模型依據 113 學年度學測英文作文評分標準：
    - **內容 (0-5)**: 主題句清楚、細節支持完整。
    - **組織 (0-5)**: 開頭發展結尾明確、轉承語使用得當。
    - **文法 (0-5)**: 句構變化豐富、文法正確。
    - **字彙 (0-5)**: 用字精確、拼字無誤。
    
    *目標中位數設定為 12 分，15 分以上為高標。*
    """)

st.title("📝 高中學測英文作文 AI 批改名師")
st.markdown("專為台灣高中生設計，提供像補習班老師一樣的「手術式」修改建議。")

# 初始化 Session State (用來記憶出題內容)
if 'generated_topic' not in st.session_state:
    st.session_state.generated_topic = ""

# 分頁設計
tab1, tab2 = st.tabs(["🎲 題目設定", "✍️ 作文批改"])

# --- Tab 1: 題目設定 ---
with tab1:
    st.subheader("題目來源")
    topic_source = st.radio("選擇題目來源", ["自行上傳/輸入題目", "請 AI 幫我出題 (食衣住行育樂)"])
    
    current_topic = ""
    
    if topic_source == "請 AI 幫我出題 (食衣住行育樂)":
        if st.button("✨ 立即生成模擬試題"):
            if not api_key:
                st.error("請先在左側輸入 API Key 才能生成題目喔！")
            else:
                try:
                    client = OpenAI(api_key=api_key)
                    prompt_gen = """
                    你現在是台灣高中英文學測的出題老師。請從「食、衣、住、行、育、樂」中隨機選一個主題，
                    設計一個符合學測格式的英文作文題目。
                    格式要求：
                    1. 題目提示：一段約 50 字的中文背景描述，貼近台灣學生生活。
                    2. 清楚列出「第一段」與「第二段」必須涵蓋的內容。
                    請直接輸出題目內容即可。
                    """
                    with st.spinner("正在絞盡腦汁出題中..."):
                        response = client.chat.completions.create(
                            model="gpt-4o-mini", # 使用較便宜快速的模型
                            messages=[{"role": "user", "content": prompt_gen}]
                        )
                        st.session_state.generated_topic = response.choices[0].message.content
        
        if st.session_state.generated_topic:
            st.success("出題完成！")
            st.markdown(st.session_state.generated_topic)
            current_topic = st.session_state.generated_topic

    else:
        current_topic = st.text_area("請輸入題目說明 (或貼上題目文字)", height=150, placeholder="例如：提示：排隊雖是生活中常有的經驗... 第一段請描述... 第二段請說明...")

# --- Tab 2: 作文批改 ---
with tab2:
    st.subheader("上傳你的作文")
    
    user_essay = st.text_area("請在此輸入你的英文作文 (建議至少 120 字)", height=300)
    
    if st.button("🚀 開始批改"):
        if not api_key:
            st.error("請先在左側輸入 API Key！")
        elif not user_essay:
            st.warning("請輸入作文內容！")
        else:
            client = OpenAI(api_key=api_key)
            
            # 核心 Prompt：結合評分標準圖片內容與教學指令
            system_prompt = f"""
            # Role
            你是一位台灣頂尖的高中英文補習班名師，專精於「大學學測英文作文」。你的評分嚴格但具備建設性。
            
            # Context
            題目：{current_topic}
            學生作文：{user_essay}
            
            # Task: Grading Rubric (依據圖片標準)
            請嚴格依據以下四個項目評分 (每項 0-5 分，滿分 20)：
            
            1. **內容 (Content)**
               - 5分：主題句清楚切題，有具體完整的細節支持。
               - 3分：主題不夠清楚或突顯，部分敘述發展不全。
               - 1-2分：大部分敘述發展不全或與主題無關。
               
            2. **組織 (Organization)**
               - 5分：重點分明，有開頭、發展、結尾，前後連貫，轉承語使用得當。
               - 3分：重點安排不妥，前後發展比例與轉承語使用欠妥。
               - 1-2分：重點不明，前後不連貫。
               
            3. **文法句構 (Grammar)**
               - 5分：全文幾無文法錯誤，文句結構富變化。
               - 3分：文法錯誤少，且未影響文意表達。
               - 1-2分：文法錯誤多，明顯影響文意表達。
               
            4. **字彙拼字 (Vocabulary)**
               - 5分：用字精確得宜，幾無拼字錯誤。
               - 3分：字詞單調重複，用字偶有不當，少許拼字錯誤。
               - 1-2分：用字拼字錯誤多，明顯影響文意表達。

            **分數控制原則**：
            - 中位數應落在 12 分左右（代表基本達意但平庸）。
            - 15 分以上為高標（內容充實、句構多樣）。
            
            # Output Format (請用繁體中文回應)
            請按照以下 Markdown 格式輸出：

            ## 📊 綜合評分: [總分]/20
            - **內容**: [分數]/5
            - **組織**: [分數]/5
            - **文法**: [分數]/5
            - **字彙**: [分數]/5

            ## 📝 老師總評
            (約 100 字，先肯定優點，再指出主要弱點，語氣像補習班名師。)

            ## 🔍 手術式批改 (重點改進)
            (請挑出 3 個最具代表性的錯誤或是「可以寫得更高級」的句子)
            
            **1. [分類：如 文法/搭配詞/句型]**
            > **原文**: "[引用原句]"
            > **❌ 問題**: (簡述問題，如：中式英文、語意不清)
            > **✅ 名師升級**: "**[修改後的句子]**"
            > **💡 解析**: (解釋使用了什麼技巧，如單字升級、倒裝句、分詞構句)

            (重複 3 次)

            ## 🚀 下一步練習建議
            (給出一個具體可執行的建議)
            """

            with st.spinner("老師正在仔細批改中，請稍候..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o", # 使用較強的模型來進行批改
                        messages=[{"role": "system", "content": system_prompt}]
                    )
                    feedback = response.choices[0].message.content
                    st.markdown(feedback)
                except Exception as e:
                    st.error(f"發生錯誤：{e}")