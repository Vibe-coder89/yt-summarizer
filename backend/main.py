from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
import os
from dotenv import load_dotenv

# Load env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client
client = Groq(api_key=GROQ_API_KEY)

# FastAPI app
app = FastAPI()


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
    return "".join(sga_map.get(char, char) for char in text.lower())


# Extract video ID
def extract_video_id(url: str):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return url


# 🔥 Summarization function
def summarize_text(text, lang, length):

    # 📏 Length control
    if length == "short":
        detail = "in 3-4 very short bullet points"

    elif length == "medium":
        detail = "in 6-8 clear bullet points"

    else:
        detail = """
        in a detailed format with:
        - 20-25 bullet points
        - Each point 4-5 lines long
        - Include explanations and key insights
        """

    # 🌍 Language handling
    if lang == "hi":
        lang_text = "Hindi"
    elif lang == "harappan":
        lang_text = "symbolic ancient Indus-style language"
    else:
        lang_text = "English"

    # 🔥 Strong prompt (prevents intro text)
    prompt = f"""
    Summarize the following transcript {detail} in {lang_text}.

    RULES:
    - Output ONLY bullet points
    - No introduction
    - No headings
    - Start directly with "- "
    - Do not write anything before or after bullets

    Transcript:
    {text[:4000]}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_summary = response.choices[0].message.content

    # 🔥 CLEANING (safe version)
    cleaned = "\n".join(
        line for line in raw_summary.split("\n")
        if line.strip().startswith("-")
    )

    # fallback if model ignored format
    return cleaned if cleaned.strip() else raw_summary



@app.get("/")
def home():
    return {"message": "API is working"}



@app.get("/summarize")
def summarize(url: str, lang: str = "en", length: str = "medium"):
    try:
        video_id = extract_video_id(url)

        api = YouTubeTranscriptApi()

        # 🎯 Try fetching transcript
        try:
            transcript = api.fetch(video_id, languages=["en"])
        except:
            try:
                transcript = api.fetch(video_id, languages=["hi"])
            except:
                return {"error": "No transcript available for this video"}

        text = " ".join([t.text for t in transcript])

        if not text.strip():
            return {"error": "Transcript is empty"}

        summary = summarize_text(text, lang, length)

        # 🎮 Minecraft conversion AFTER AI
        if lang == "minecraft":
            summary = to_enchanting(summary)

        return {"summary": summary}

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}
