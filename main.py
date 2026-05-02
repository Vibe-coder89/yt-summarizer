from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
from dotenv import load_dotenv
import yt_dlp
import requests

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

# 🎮 Minecraft mapping
sga_map = {
    "a":"ᔑ","b":"ʖ","c":"ᓵ","d":"↸","e":"ᒷ","f":"⎓","g":"⊣",
    "h":"⍑","i":"╎","j":"⋮","k":"ꖌ","l":"ꖎ","m":"ᒲ","n":"リ",
    "o":"𝙹","p":"!¡","q":"ᑑ","r":"∷","s":"ᓭ","t":"ℸ","u":"⚍",
    "v":"⍊","w":"∴","x":" ̇/","y":"||","z":"⨅"
}

def to_enchanting(text):
    return "".join(sga_map.get(c, c) for c in text.lower())


# 🔥 Extract video ID
def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url


# 🔥 Transcript via yt-dlp metadata (lightweight)
def get_transcript(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        subtitles = info.get("subtitles") or info.get("automatic_captions")

        if not subtitles:
            return None

        # Try English captions
        en_subs = subtitles.get("en") or subtitles.get("en-US")

        if not en_subs:
            return None

        sub_url = en_subs[0]["url"]

        res = requests.get(sub_url)
        data = res.text

        # Clean subtitle text
        lines = data.split("\n")
        text = " ".join(
            line for line in lines
            if line and "-->" not in line and not line.isdigit() and "WEBVTT" not in line
        )

        return text.strip()

    except Exception as e:
        print("TRANSCRIPT ERROR:", e)
        return None


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

        text = get_transcript(video_id)

        if not text:
            return {
                "error": "Captions not accessible for this video (try another)"
            }

        summary = summarize_text(text, lang, length)

        if lang == "minecraft":
            summary = to_enchanting(summary)

        return {"summary": summary}

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Something went wrong"}