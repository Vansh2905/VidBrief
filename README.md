# 🎬 VidBrief - AI-Powered YouTube Video Intelligence

**VidBrief** is a high-speed, agentic AI tool that converts long YouTube videos into structured, actionable insights in seconds. Powered by [Agno](https://github.com/agno-agi/agno) and ultra-fast [Groq](https://groq.com) inference (Llama 3.3 70B & Llama 3.1 8B), VidBrief generates precise timestamps, comprehensive overviews, key takeaways, and lets you interactively chat with any video.

---

## ✨ Key Features

- **⏱️ Timestamped Breakdown**: Automatic segmentation with precise timestamps linking to major topic shifts and demonstrations.
- **🎯 Multiple Analysis Modes**:
  - **Comprehensive Breakdown**: Full overview, structured timeline, key learning points, and conclusions.
  - **Quick TL;DR**: 3–5 bullet point executive summary for rapid scanning.
  - **Actionable Takeaways & Tools**: Highlights tools, repositories, tips, and step-by-step implementations.
  - **Study Notes & Quiz**: Generates concept glossaries, study outlines, and self-test quizzes with answer keys.
- **⚡ Real-time Streaming**: Instant feedback with live typewriter output via Groq's low-latency inference.
- **📺 Side-by-Side Video Player**: Embedded video player allows you to watch and verify moments alongside generated notes.
- **💬 Interactive Video Chat (Q&A)**: Ask follow-up questions directly to the video assistant.
- **📥 One-Click Export**: Download structured reports as clean Markdown (`.md`) files.

---

## 🛠️ Tech Stack

- **Agent Framework**: [Agno](https://github.com/agno-agi/agno)
- **LLM Provider**: [Groq](https://groq.com) (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, etc.)
- **Video Transcript Engine**: `youtube-transcript-api` via Agno's `YouTubeTools`
- **UI Framework**: [Streamlit](https://streamlit.io/)

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- A [Groq API Key](https://console.groq.com/) (free tier available)

### 2. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Vansh2905/VidBrief.git
cd VidBrief

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the Application

Launch the Streamlit web app:

```bash
streamlit run ui.py
```

---

## 💡 Usage Guide

1. Paste any public YouTube video link (e.g., tutorials, podcasts, lectures, tech talks).
2. Select your preferred **Analysis Mode** from the sidebar (e.g. *Comprehensive Breakdown* or *Quick TL;DR*).
3. Click **🚀 Analyze** and watch the report stream live.
4. Download the generated report as Markdown or ask follow-up questions in the **💬 Ask Questions** chat section.

---

## ⚠️ Notes

- **Captions Required**: VidBrief uses video transcripts. Ensure that the YouTube video has closed captions (CC) or auto-generated subtitles enabled.
