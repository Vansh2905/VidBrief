import os
import re
import streamlit as st
import importlib
import agent
importlib.reload(agent)

from agent import (
    build_agent,
    build_qa_agent,
    DEFAULT_MODEL,
    ANALYSIS_MODES,
)

# Page Configuration
st.set_page_config(
    page_title="VidBrief - AI YouTube Video Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verify GROQ_API_KEY from environment
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("⚠️ `GROQ_API_KEY` is not configured in the `.env` file. Please set it in `.env` to use VidBrief.")
    st.stop()

# Friendly display names for available models
MODEL_DISPLAY_NAMES = {
    "openai/gpt-oss-120b": "OpenAI GPT-OSS 120B (High Reasoning - Default)",
    "openai/gpt-oss-20b": "OpenAI GPT-OSS 20B (Fast & Lightweight)",
    "qwen/qwen3.8-27b": "Qwen 3.8 27B",
    "qwen/qwen3.6-27b": "Qwen 3.6 27B",
    "groq/compound": "Groq Compound",
    "groq/compound-mini": "Groq Compound Mini",
    "allam-2-7b": "ALLaM 2 7B",
}

# Cache model list discovery so it doesn't query the Groq API on every rerun
@st.cache_data(ttl=3600)
def fetch_cached_models() -> list[str]:
    if hasattr(agent, "get_available_models"):
        return agent.get_available_models()
    return [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "groq/compound",
    ]

available_models = fetch_cached_models()

# Custom Styling
st.markdown("""
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8F00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        color: #718096;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: rgba(255, 75, 75, 0.05);
        border: 1px solid rgba(255, 75, 75, 0.2);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)


def extract_youtube_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/embed\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            return match.group(1)
    return None


# Initialize Session State
if "report" not in st.session_state:
    st.session_state.report = None
if "analyzed_url" not in st.session_state:
    st.session_state.analyzed_url = ""
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_mode" not in st.session_state:
    st.session_state.active_mode = "Comprehensive Breakdown"
if "model_used" not in st.session_state:
    st.session_state.model_used = DEFAULT_MODEL
if "selected_model_id" not in st.session_state:
    st.session_state.selected_model_id = (
        DEFAULT_MODEL if DEFAULT_MODEL in available_models else available_models[0]
    )
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "Comprehensive Breakdown"


# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings & Options")
    
    # Model Selector with persistent state
    selected_model_id = st.selectbox(
        "🧠 Groq Model",
        options=available_models,
        key="selected_model_id",
        format_func=lambda m: MODEL_DISPLAY_NAMES.get(m, m),
        help="Switch between models available on your Groq account."
    )
    
    # Analysis Mode Selector
    selected_mode = st.selectbox(
        "🎯 Analysis Mode",
        options=list(ANALYSIS_MODES.keys()),
        key="selected_mode",
        help="Choose how in-depth and structured the report should be."
    )
    
    st.markdown("---")
    st.markdown("### 💡 About VidBrief")
    st.markdown(
        "VidBrief extracts multilingual transcripts from YouTube videos and leverages Groq's "
        "ultra-fast inference to generate structured timestamps, summaries, and actionable insights."
    )
    
    if st.session_state.report:
        if st.button("🗑️ Clear Current Analysis"):
            st.session_state.report = None
            st.session_state.analyzed_url = ""
            st.session_state.video_id = None
            st.session_state.chat_history = []
            st.session_state.model_used = selected_model_id
            st.rerun()


# Header Section
st.markdown('<div class="main-title">🎬 VidBrief</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Powered YouTube Video Intelligence & Timestamp Generator</div>',
    unsafe_allow_html=True
)

# Input Section
col_input, col_btn = st.columns([5, 1])
with col_input:
    video_url = st.text_input(
        "Enter YouTube Video Link",
        placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/...",
        value=st.session_state.analyzed_url if st.session_state.analyzed_url else "",
        label_visibility="collapsed"
    )
with col_btn:
    analyze_clicked = st.button("🚀 Analyze", use_container_width=True, type="primary")


def run_analysis(target_url: str, model_id: str, mode: str):
    """Run video analysis using the selected model and mode."""
    video_id = extract_youtube_video_id(target_url)
    if not video_id:
        st.error("Invalid YouTube URL. Please provide a valid YouTube link.")
        return

    st.session_state.video_id = video_id
    st.session_state.analyzed_url = target_url
    st.session_state.active_mode = mode
    st.session_state.model_used = model_id
    st.session_state.chat_history = []  # Reset chat for new analysis
    
    try:
        agent = build_agent(
            model_id=model_id,
            mode=mode
        )
        
        display_name = MODEL_DISPLAY_NAMES.get(model_id, model_id)
        with st.spinner(f"🔍 Analyzing video with {display_name}..."):
            prompt = (
                f"Analyze this YouTube video: {target_url}\n"
                f"Apply the '{mode}' guidelines strictly."
            )
            
            # Stream or run response
            try:
                response_stream = agent.run(prompt, stream=True)
                report_placeholder = st.empty()
                accumulated_text = ""
                
                for chunk in response_stream:
                    chunk_content = getattr(chunk, "content", None)
                    if chunk_content is not None:
                        accumulated_text += chunk_content
                    elif isinstance(chunk, str):
                        accumulated_text += chunk
                    report_placeholder.markdown(accumulated_text + "▌")
                
                report_placeholder.markdown(accumulated_text)
                st.session_state.report = accumulated_text
            except Exception:
                # Non-streaming fallback
                response = agent.run(prompt)
                st.session_state.report = response.content

        st.success("✅ Analysis generated successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to analyze video: {str(e)}")
        st.info(
            "Note: Ensure the YouTube video has subtitles/captions enabled. "
            "Videos without transcripts cannot be read by the transcript tool."
        )


# Trigger Analysis on Button Click
if analyze_clicked:
    if not video_url.strip():
        st.error("Please enter a valid YouTube video URL.")
    else:
        run_analysis(video_url.strip(), selected_model_id, selected_mode)


# Display Output & Interactive Workspace
if st.session_state.report and st.session_state.analyzed_url:
    st.markdown("---")
    
    # Prompt to re-analyze if user changed model or mode in sidebar
    if (selected_model_id != st.session_state.model_used) or (selected_mode != st.session_state.active_mode):
        new_model_name = MODEL_DISPLAY_NAMES.get(selected_model_id, selected_model_id)
        st.info(
            f"💡 You switched settings in the sidebar (Model: **{new_model_name}** | Mode: **{selected_mode}**)."
        )
        if st.button(f"🔄 Re-analyze with {new_model_name} ({selected_mode})", type="secondary"):
            run_analysis(st.session_state.analyzed_url, selected_model_id, selected_mode)
    
    # Side-by-side Layout: Video Player + Analysis Report
    col_video, col_report = st.columns([1, 1.4], gap="large")
    
    with col_video:
        st.subheader("📺 Video Preview")
        st.video(st.session_state.analyzed_url)
        
        st.markdown(
            f"""
            <div class="metric-card">
                <b>Mode:</b> {st.session_state.active_mode}<br>
                <b>Model:</b> <code>{st.session_state.model_used}</code><br>
                <b>Video ID:</b> <code>{st.session_state.video_id}</code>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Download Report Action
        st.download_button(
            label="📥 Download Markdown Report",
            data=st.session_state.report,
            file_name=f"VidBrief_{st.session_state.video_id}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        with st.expander("📋 View Raw Markdown"):
            st.code(st.session_state.report, language="markdown")

    with col_report:
        st.subheader("📑 Analysis Report")
        st.markdown(st.session_state.report)

    # Follow-up Interactive Q&A Section
    st.markdown("---")
    st.subheader("💬 Ask Questions About This Video")
    st.caption("Ask specific follow-up questions, request timestamp clarification, or dive deeper into any topic covered.")

    # Render previous conversation
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_query = st.chat_input("Ask something about this video...")
    if user_query:
        # Display user question
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Run QA Agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    qa_agent = build_qa_agent(model_id=st.session_state.model_used)
                    qa_prompt = (
                        f"Video URL: {st.session_state.analyzed_url}\n\n"
                        f"Previous Analysis Summary:\n{st.session_state.report[:2000]}\n\n"
                        f"User Question: {user_query}"
                    )
                    qa_response = qa_agent.run(qa_prompt)
                    answer = qa_response.content
                    st.markdown(answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as ex:
                    err_msg = f"Sorry, I couldn't answer that: {str(ex)}"
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})