from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
import os
from dotenv import load_dotenv

# Load env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Extract video ID
def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url


# Get transcript
def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except:
        return None


# Summarize
def summarize_text(text, lang, length):
    if length == "short":
        detail = "in 3-4 bullet points"
    elif length == "medium":
        detail = "in 6-8 bullet points"
    else:
        detail = "in 10-12 detailed bullet points"

    if lang == "hi":
        language = "Hindi"
    else:
        language = "English"

    prompt = f"""
    Summarize this transcript {detail} in {language}.

    Rules:
    - Only bullet points
    - No intro
    - Start with "- "

    Transcript:
    {text[:4000]}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


@app.get("/")
def home():
    return {"message": "API working"}


@app.get("/summarize")
def summarize(url: str, lang: str = "en", length: str = "medium"):
    video_id = extract_video_id(url)

    text = get_transcript(video_id)

    if not text:
        return {"error": "No transcript available for this video"}

    summary = summarize_text(text, lang, length)

    return {"summary": summary}