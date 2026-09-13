import os
import re
from textwrap import dedent
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import Toolkit
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

# Default Groq model for this account
DEFAULT_MODEL = "openai/gpt-oss-120b"

# Fallback model list if API fetch is unavailable
FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "groq/compound",
    "groq/compound-mini",
]

def get_available_models(api_key: str | None = None) -> list[str]:
    """Dynamically fetch all chat-capable models available to the current Groq API key."""
    resolved_key = api_key or os.getenv("GROQ_API_KEY")
    if not resolved_key:
        return FALLBACK_MODELS
    try:
        from groq import Groq as GroqClient
        client = GroqClient(api_key=resolved_key)
        all_models = client.models.list().data
        
        # Filter for text/chat generation models (exclude whisper, guard, audio models)
        excluded_keywords = ["whisper", "guard", "orpheus", "safeguard"]
        chat_models = [
            m.id for m in all_models 
            if not any(kw in m.id.lower() for kw in excluded_keywords)
        ]
        
        # Ensure DEFAULT_MODEL is at the very top if available
        if DEFAULT_MODEL in chat_models:
            chat_models.remove(DEFAULT_MODEL)
            chat_models.insert(0, DEFAULT_MODEL)
            
        return chat_models if chat_models else FALLBACK_MODELS
    except Exception:
        return FALLBACK_MODELS


class SmartYouTubeTools(Toolkit):
    """Enhanced YouTube toolkit that supports multilingual transcripts (Hindi, English, etc.)
    and smart windowing to prevent LLM token-per-minute overflow.
    """
    def __init__(self):
        super().__init__(name="smart_youtube_tools")
        self.register(self.get_video_transcript_and_timeline)

    def get_video_transcript_and_timeline(self, url: str) -> str:
        """Fetch chronological transcript milestones and key timestamp transitions for any YouTube video.
        Automatically retrieves English, Hindi, and 15+ other languages.
        """
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url.strip())
        video_id = match.group(1) if match else url.strip()
        
        supported_langs = [
            "en", "hi", "es", "fr", "de", "zh", "ja", "ru",
            "pt", "ar", "bn", "ta", "te", "mr", "gu", "ur", "kn", "ml"
        ]
        
        try:
            captions = YouTubeTranscriptApi().fetch(video_id, languages=supported_langs)
        except Exception as e:
            return f"Error retrieving captions: {str(e)}"
            
        total_lines = len(captions)
        if total_lines == 0:
            return "No captions found for this video."

        # Keep output compact to fit comfortably within Groq TPM limits (under 2,000 tokens)
        step = max(1, total_lines // 100)
        sampled = []
        for i in range(0, total_lines, step):
            item = captions[i]
            start = int(item.start)
            m, s = divmod(start, 60)
            h, m = divmod(m, 60)
            ts = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
            sampled.append(f"[{ts}] {item.text}")

        return "\n".join(sampled[:120])


# Mode instruction presets
ANALYSIS_MODES = {
    "Comprehensive Breakdown": dedent("""\
        You are an expert YouTube content analyst with a keen eye for detail!
        Follow these steps for comprehensive video analysis:
        1. Video Overview:
           - Video topic, purpose, and target audience
           - Video category (e.g., Educational, Technical, Gaming, Tech Review, Creative)
        2. Structured Timestamped Breakdown:
           - Create precise, sequential timestamps for major topic transitions
           - Format each segment as: **[MM:SS - MM:SS] Segment Title**
           - Include a bulleted breakdown of what was covered in that segment
        3. Key Takeaways & Practical Insights:
           - Highlight core concepts, methodologies, or frameworks demonstrated
           - Mention any tools, libraries, or resources referenced
        4. Final Executive Conclusion:
           - A concise synthesis of the video's primary value proposition
    """),
    
    "Quick TL;DR": dedent("""\
        You are a concise executive summarizer.
        Provide a rapid, high-impact digest of this video:
        1. TL;DR (3-4 sentences summarizing the core message)
        2. Top 5 Key Insights (bulleted, punchy, and clear)
        3. Who Should Watch This (target audience and difficulty level)
        4. Most Important Moments (top 2-3 timestamped highlights)
    """),
    
    "Actionable Takeaways & Tools": dedent("""\
        You are a pragmatic productivity and implementation coach.
        Analyze this video focusing strictly on actionable knowledge:
        1. Action Items (step-by-step actions the viewer can immediately execute)
        2. Tools & Resources Mentioned (software, websites, libraries, books, or hardware)
        3. Common Pitfalls & Mistakes to Avoid (based on the speaker's advice)
        4. Best Quotes or Rules of Thumb
    """),
    
    "Study Notes & Quiz": dedent("""\
        You are an academic tutor and educator.
        Turn this video into structured study material:
        1. Key Concept Definitions (glossary of core terms introduced)
        2. Detailed Study Outline (concept hierarchy and relationships)
        3. Self-Assessment Quiz (3-5 conceptual or practical questions)
        4. Answer Key (detailed explanations for the quiz questions)
    """)
}


def get_groq_model(model_id: str = DEFAULT_MODEL, api_key: str | None = None) -> Groq:
    """Instantiate a Groq model instance with optional custom API key."""
    resolved_key = api_key or os.getenv("GROQ_API_KEY")
    if not resolved_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Please set it in your .env file."
        )
    return Groq(id=model_id, api_key=resolved_key)


def build_agent(
    model_id: str = DEFAULT_MODEL,
    mode: str = "Comprehensive Breakdown",
    api_key: str | None = None
) -> Agent:
    """Build and return an Agno Agent tailored to the selected analysis mode."""
    instructions = ANALYSIS_MODES.get(mode, ANALYSIS_MODES["Comprehensive Breakdown"])
    
    guidelines = dedent("""\
        Multilingual Processing & Quality Guidelines:
        - The transcript may be in English, Hindi, Hinglish, or any other language.
        - You are fully authorized and expected to process non-English/Hindi transcripts.
        - Synthesize, translate, and present the final output in clear, fluent English.
        - Retain technical terminology, code references, formulas, and tool names accurately.
        - Verify timestamp accuracy based strictly on the video timeline.
        - Avoid hallucinating timestamps or claims not made in the video.
    """)

    return Agent(
        name="VidBrief",
        model=get_groq_model(model_id=model_id, api_key=api_key),
        tools=[SmartYouTubeTools()],
        instructions=f"{instructions}\n\n{guidelines}",
        add_datetime_to_context=True,
        markdown=True
    )


def build_qa_agent(
    model_id: str = DEFAULT_MODEL,
    api_key: str | None = None
) -> Agent:
    """Build a conversational Q&A Agent for answering follow-up questions about a video."""
    return Agent(
        name="VidBrief-QA",
        model=get_groq_model(model_id=model_id, api_key=api_key),
        tools=[SmartYouTubeTools()],
        instructions=dedent("""\
            You are a helpful video assistant. Your role is to answer user follow-up questions
            accurately based on the video content, transcript, and previous analysis.
            - Answer clearly and concisely in English.
            - Videos may be in Hindi/Hinglish or other languages; translate and answer accurately.
            - Reference specific video timestamps where applicable (e.g., [03:45]).
            - If the video does not contain information to answer the question, state so honestly.
        """),
        add_datetime_to_context=True,
        markdown=True
    )