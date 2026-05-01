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

# Whisper + download
import whisper
import yt_dlp

# Load env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Clients
client = Groq(api_key=GROQ_API_KEY)

# ⚠️ load small model (important for Render)
whisper_model = whisper.load_model("base")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎮 Minecraft mapping
sga_map = {
    "a":"ᔑ","b":"ʖ","c":"ᓵ","d":"↸","e":"ᒷ","f":"⎓","g":"⊣",
    "h":"⍑","i":"╎","j":"⋮","k":"ꖌ","l":"ꖎ","m":"ᒲ","n":"リ",
    "o":"𝙹","p":"!¡","q":"ᑑ","r":"∷","s":"ᓭ","t":"ℸ","u":"⚍",
    "v":"⍊","w":"∴","x":" ̇/","y":"||","z":"⨅"
}

def to_enchanting(text):
    return "".join(sga_map.get(c, c) for c in text.lower())


# Extract video id
def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url


# 🔥 Transcript (with retry)
def get_transcript(video_id):
    for _ in range(3):
        try:
            tl = YouTubeTranscriptApi.list_transcripts(video_id)

            try:
                t = tl.find_transcript(['en'])
            except:
                t = tl.find_generated_transcript(['en'])

            data = t.fetch()
            return " ".join([x['text'] for x in data])

        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except:
            time.sleep(2)

    return None


# 🔥 Download audio
def download_audio(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# 🔥 Whisper transcription
def transcribe_audio(file_path):
    result = whisper_model.transcribe(file_path)
    return result["text"]


# 🔥 Summarization
def summarize_text(text, lang, length):

    if length == "short":
        detail = "in 3-4 very short bullet points"
    elif length == "medium":
        detail = "in 6-8 clear bullet points"
    else:
        detail = "in 10-15 detailed bullet points"

    if lang == "hi":
        lang_text = "Hindi"
    elif lang == "harappan":
        lang_text = "symbolic ancient Indus-style language"
    else:
        lang_text = "English"

    prompt = f"""
    Summarize the following transcript {detail} in {lang_text}.

    RULES:
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

    raw = response.choices[0].message.content

    cleaned = "\n".join(
        line for line in raw.split("\n")
        if line.strip().startswith("-")
    )

    return cleaned if cleaned.strip() else raw


@app.get("/")
def home():
    return {"message": "API is working"}


@app.get("/summarize")
def summarize(url: str, lang: str = "en", length: str = "medium"):
    try:
        video_id = extract_video_id(url)

        # 1️⃣ Try transcript first
        text = get_transcript(video_id)

        # 2️⃣ Whisper fallback
        if not text:
            try:
                audio_file = download_audio(video_id)
                text = transcribe_audio(audio_file)
                os.remove(audio_file)
            except:
                return {
                    "error": "Could not process this video (transcript + audio failed)"
                }

        summary = summarize_text(text, lang, length)

        if lang == "minecraft":
            summary = to_enchanting(summary)

        return {"summary": summary}

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Something went wrong"}