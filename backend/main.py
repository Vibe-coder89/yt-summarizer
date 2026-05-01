from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound
)
from groq import Groq
import os
import time
from dotenv import load_dotenv

# Load env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client
client = Groq(api_key=GROQ_API_KEY)

# FastAPI app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎮 Minecraft Enchanting mapping
sga_map = {
    "a":"ᔑ","b":"ʖ","c":"ᓵ","d":"↸","e":"ᒷ","f":"⎓","g":"⊣",
    "h":"⍑","i":"╎","j":"⋮","k":"ꖌ","l":"ꖎ","m":"ᒲ","n":"リ",
    "o":"𝙹","p":"!¡","q":"ᑑ","r":"∷","s":"ᓭ","t":"ℸ","u":"⚍",
    "v":"⍊","w":"∴","x":" ̇/","y":"||","z":"⨅"
}

def to_enchanting(text):
    return "".join(sga_map.get(c, c) for c in text.lower())


# 🔹 Extract video ID
def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url


# 🔥 Robust transcript fetch with retry
def get_transcript(video_id):
    for attempt in range(3):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                transcript = transcript_list.find_generated_transcript(['en'])

            data = transcript.fetch()
            return " ".join([t['text'] for t in data])

        except (TranscriptsDisabled, NoTranscriptFound):
            return None

        except Exception:
            time.sleep(2 + attempt)  # backoff retry

    return None


# 🔥 Summarization
def summarize_text(text, lang, length):

    # Length control
    if length == "short":
        detail = "in 3-4 very short bullet points"
    elif length == "medium":
        detail = "in 6-8 clear bullet points"
    else:
        detail = """
        in a detailed format with:
        - 10-15 bullet points
        - Each point 2-3 lines long
        - Include explanations and key insights
        """

    # Language
    if lang == "hi":
        lang_text = "Hindi"
    elif lang == "harappan":
        lang_text = "symbolic ancient Indus-style language"
    else:
        lang_text = "English"

    prompt = f"""
    Summarize the following transcript {detail} in {lang_text}.

    RULES:
    - Output ONLY bullet points
    - No introduction
    - No headings
    - Start directly with "- "

    Transcript:
    {text[:4000]}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content

    # Clean output
    cleaned = "\n".join(
        line for line in raw.split("\n")
        if line.strip().startswith("-")
    )

    return cleaned if cleaned.strip() else raw


# Home
@app.get("/")
def home():
    return {"message": "API is working"}


# 🔥 Main route
@app.get("/summarize")
def summarize(url: str, lang: str = "en", length: str = "medium"):
    try:
        video_id = extract_video_id(url)

        text = get_transcript(video_id)

        if not text:
            return {
                "error": "Transcript unavailable or rate-limited. Try another video or try again."
            }

        summary = summarize_text(text, lang, length)

        if lang == "minecraft":
            summary = to_enchanting(summary)

        return {"summary": summary}

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Something went wrong"}