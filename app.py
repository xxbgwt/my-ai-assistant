import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from duckduckgo_search import DDGS  # 👈 新引入的搜索工具

# 1. 页面配置
st.set_page_config(page_title="DeepSeek 全能版", page_icon="🌍", layout="wide")

# ==========================================
# 🔐 门禁系统 (你自己设的密码)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def check_password():
    if st.session_state.password_input == "888888":  # 🔴 你的密码
        st.session_state.logged_in = True
    else:
        st.error("密码错误 ❌")

if not st.session_state.logged_in:
    st.markdown("## 🔒 请输入访问密码")
    st.text_input("Password", type="password", key="password_input", on_change=check_password)
    st.stop()

# ==========================================
# 👇 主程序开始
# ==========================================

st.title("🌍 DeepSeek 全能助手 (联网版)")

# 2. 配置 API (🔴 填你的 Key)
client = OpenAI(
    api_key="sk-c65fe0d9907d409086578b3de6cab3e0",
    base_url="https://api.deepseek.com"
)

# 初始化消息
if "messages" not in st.session_state:
    st.session_state.messages = []

# === 🎛️ 侧边栏 ===
with st.sidebar:
    st.header("🎛️ 能力开关")
    
    # 🔥 新功能：联网开关
    enable_web = st.toggle("🌐 开启联网搜索", value=False, help="开启后，AI 会先搜索互联网再回答，适合问新闻/实时信息。")
    
    st.divider()
    
    creativity = st.slider("🧠 创造力", 0.0, 1.3, 0.7)
    
    st.divider()
    
    uploaded_file = st.file_uploader("📂 上传文档 (RAG)", type=["pdf", "txt"])
    file_content = ""
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".pdf"):
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    file_content += page.extract_text() or ""
            else:
                file_content = uploaded_file.read().decode("utf-8")
            st.success(f"已加载: {uploaded_file.name}")
        except:
            st.error("读取失败")

    st.divider()
    if st.button("🗑️ 清空记录"):
        st.session_state.messages = []
        st.rerun()

# === 聊天主逻辑 ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请输入问题..."):
    
    # 1. 显示用户问题
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 准备上下文
    final_messages = []
    system_context = "你是一个智能助手。"

    # === 🕵️‍♂️ 核心逻辑：处理联网搜索 ===
    if enable_web:
        # 显示一个状态条，让用户知道正在搜
        with st.status("🕵️‍♂️ 正在搜索互联网...", expanded=True) as status:
            try:
                # 调用 DuckDuckGo 搜索
                results = DDGS().text(prompt, max_results=3)
                if results:
                    web_content = ""
                    for i, res in enumerate(results):
                        st.write(f"📄 **来源 {i+1}**: [{res['title']}]({res['href']})")
                        web_content += f"来源[{i+1}]: {res['body']}\n"
                    
                    # 把搜到的内容喂给 AI
                    system_context = f"""
                    你是一个具有联网能力的助手。
                    请根据以下的【互联网搜索结果】来回答用户的问题。
                    记得在回答中引用来源。
                    
                    【搜索结果】：
                    {web_content}
                    """
                    status.update(label="✅ 搜索完成！", state="complete", expanded=False)
                else:
                    status.update(label="⚠️ 没搜到相关信息，将直接回答。", state="complete")
            except Exception as e:
                status.update(label=f"❌ 搜索出错: {e}", state="error")
    
    # === 处理文档上下文 ===
    if file_content:
        system_context += f"\n\n此外，请参考以下【本地文档】内容：\n{file_content}"

    # 组装最终的 Prompt
    final_messages.append({"role": "system", "content": system_context})
    final_messages.extend(st.session_state.messages)

    # 3. AI 回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=final_messages,
                temperature=creativity,
                stream=True 
            )
            response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"出错: {e}")