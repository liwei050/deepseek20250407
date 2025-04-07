import streamlit as st
from openai import OpenAI
import time
import os

# from transformers import AutoTokenizer, AutoModelForCausalLM


# 清除可能导致proxies错误的環境变量
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

# 页面配置
# 尝试多种图标设置方式，提高兼容性
try:
    # 方法1：使用emoji字符
    st.set_page_config(
        page_title="人力资源助理大模型",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    try:
        # 方法2：使用在线图片URL
        st.set_page_config(
            page_title="人力资源助理大模型",
            page_icon="https://emoji.aranja.com/static/emoji-data/img-apple-160/1f916.png",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except Exception as e:
        # 方法3：使用默认图标
        st.set_page_config(
            page_title="人力资源助理大模型",
            layout="wide",
            initial_sidebar_state="expanded"
        )

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = "sk-056383c136704516ad7f09b05f2e418c"

if "base_url" not in st.session_state:
    st.session_state.base_url = "https://api.deepseek.com"

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a professional Human Resources (HR) analysis assistant specialized in answering questions related to HR management.  \n\n**Workflow:**  \n\n1. **Determine Question Type**: First, analyze whether the user's question falls under the HR domain, including but not limited to:  \n   - Recruitment & Interviewing  \n   - Employee Training & Development  \n   - Compensation & Benefits  \n   - Performance Management  \n   - Employee Relations & Communication  \n   - Labor Law & Compliance  \n   - Organizational Development & Talent Management  \n\n2. **Non-HR Question Handling**: If the question is unrelated to HR (e.g., programming, math, entertainment), respond with:  \n   \"I am an HR analysis model. Please enter an HR-related question.\"  \n\n3. **HR Question Handling**: If the question is HR-related, provide a professional, clear, and practical answer."

# 初始化文件上传区域显示状态
if "show_file_uploader" not in st.session_state:
    st.session_state.show_file_uploader = False

# 初始化模型类型
if "model_type" not in st.session_state:
    st.session_state.model_type = "online"  # 默认使用在线模型

# 初始化本地模型参数
if "local_model" not in st.session_state:
    st.session_state.local_model = "deepseek-r1:1.5b"  # 默认本地模型

# 侧边栏 - 参数设置
with st.sidebar:
    st.title("⚙️ 超参设置")

    # 简历分析按钮
    if st.button("📄 简历分析"):
        st.session_state.show_file_uploader = not st.session_state.show_file_uploader
        st.rerun()

    # 显示当前文件上传区域状态
    status = "显示" if st.session_state.show_file_uploader else "隐藏"
    st.caption(f"文件上传区域状态: {status}")

    st.markdown("---")

    # 模型参数设置
    st.session_state.max_tokens = st.slider(
        "📏 最大长度",
        min_value=1,
        max_value=32768,
        value=2048,
        step=1
    )

    st.session_state.temperature = st.slider(
        "🌡️ 采样温度",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.01
    )

    st.session_state.top_p = st.slider(
        "📊 核采样率",
        min_value=0.0,
        max_value=1.0,
        value=0.9,
        step=0.01
    )

    # 系统提示词设置
    st.session_state.system_prompt = st.text_area(
        "💬 系统提示",
        value=st.session_state.system_prompt,
        height=100
    )

    # 模型类型切换
    st.markdown("---")
    st.subheader("🔄 模型类型切换")
    model_type = st.radio(
        "选择模型类型",
        options=["在线模型", "本地模型"],
        index=0 if st.session_state.model_type == "online" else 1,
        horizontal=True
    )

    # 根据选择更新模型类型
    if model_type == "在线模型":
        st.session_state.model_type = "online"
    else:
        st.session_state.model_type = "local"

    # API设置
    with st.expander("🔑 在线模型设置"):
        st.session_state.api_key = st.text_input(
            "API Key",
            value=st.session_state.api_key,
            type="password"
        )
        st.session_state.base_url = st.text_input(
            "API URL",
            value=st.session_state.base_url
        )
    # 本地模型设置
    if st.session_state.model_type == "local":
        with st.expander("🔧 本地模型设置", expanded=True):
            st.session_state.local_model = st.selectbox(
                "本地模型",
                ["deepseek-r1:1.5b", "llama3.2:1b", "mistral", "mixtral", "qwen"],
                index=0
            )
            st.caption("使用Ollama提供的本地模型服务，确保已启动Ollama并下载相应模型")

    st.markdown("---")
    # 清空聊天按钮
    if st.button("🗑️ 清空聊天记录"):
        st.session_state.messages = []
        st.rerun()  # 将 experimental_rerun() 替换为 rerun()

# 主界面 - 聊天区域
st.title("🤖 人力资源助理大模型 🤖")

# 显示模型信息
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔍 版本: 人力资源Ver1.0")
with col2:
    st.caption("👤 作者: 李伟")
with col3:
    st.caption("📧 邮箱: 418472275@qq.com")

# 显示当前使用的模型类型
model_status = "🌐 在线模型: DeepSeek" if st.session_state.model_type == "online" else f"💻 本地模型: {st.session_state.local_model}"
st.info(model_status)

st.markdown("---")
# 对话区域
with st.chat_message("assistant"):
    st.markdown("👋 你好，我是人力资源助理大模型，请问有什么可以帮助你的吗？")

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
user_input = st.chat_input("请输入人力资源类问题")

# 根据会话状态条件性地显示文件上传功能
if st.session_state.show_file_uploader:
    # 添加文件上传功能
    uploaded_file = st.file_uploader("上传相关文档（可选）", type=["pdf", "docx", "txt", "xlsx"])

    # 显示上传文件信息
    if uploaded_file is not None:
        file_details = {
            "文件名": uploaded_file.name,
            "文件类型": uploaded_file.type,
            "文件大小": f"{uploaded_file.size / 1024:.2f} KB"
        }
        st.write("**已上传文件信息:**")
        for key, value in file_details.items():
            st.write(f"- {key}: {value}")

        # 将文件信息添加到用户输入中
        if user_input:
            user_input += f"\n\n[用户上传了文件: {uploaded_file.name}]"
else:
    # 当文件上传区域隐藏时，确保uploaded_file变量存在但为None
    uploaded_file = None

# 处理用户输入
if user_input:
    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)

    # 显示助手消息（带加载动画）
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # 创建OpenAI客户端
            if st.session_state.model_type == "online":
                # 使用在线DeepSeek模型
                client = OpenAI(
                    api_key=st.session_state.api_key,
                    base_url=st.session_state.base_url
                )
                model_name = "deepseek-chat"
            else:
                # 使用本地Ollama模型
                try:
                    client = OpenAI(
                        api_key="ollama",  # 任意值，Ollama不检查API密钥
                        base_url="http://localhost:11434/v1"
                    )
                    # 定义模型名称 - 确保在try块内提前定义
                    model_name = st.session_state.local_model
                    # 测试连接是否成功
                    client.models.list()

                except Exception as local_err:
                    st.error(f"连接本地Ollama服务失败: {str(local_err)}")
                    st.warning(
                        "请确保已启动Ollama服务，并且可以通过 http://localhost:11434 访问。如果问题持续，请切换到在线模型。")
                    message_placeholder.markdown(f"❌ 本地模型连接错误: 无法连接到Ollama服务，请确保Ollama已启动并运行。")
                    # return

            # 注意：新版本OpenAI库不再支持直接修改proxies属性
            # 如果需要设置代理，应在环境变量中配置

            # 准备消息历史
            messages = [
                {"role": "system", "content": st.session_state.system_prompt}
            ]

            # 添加聊天历史
            for msg in st.session_state.messages:
                if msg["role"] != "system":
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # 调用API
            if st.session_state.get("stream", True):
                # 流式响应
                response_stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=st.session_state.max_tokens,
                    temperature=st.session_state.temperature,
                    top_p=st.session_state.top_p,
                    stream=True
                )

                # 显示流式响应
                for chunk in response_stream:
                    if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                        content_chunk = chunk.choices[0].delta.content
                        full_response += content_chunk
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)  # 添加小延迟使流式效果更明显

                message_placeholder.markdown(full_response)
            else:
                # 非流式响应
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=st.session_state.max_tokens,
                    temperature=st.session_state.temperature,
                    top_p=st.session_state.top_p,
                    stream=False
                )

                full_response = response.choices[0].message.content
                message_placeholder.markdown(full_response)

            # 添加助手回复到历史
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            message_placeholder.markdown(f"❌ 错误: {str(e)}")
