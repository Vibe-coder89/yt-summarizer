from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client
client = Groq(api_key=GROQ_API_KEY)

# FastAPI app
app = FastAPI()

# CORS (allow frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎮 Minecraft language mapping
sga_map = {
    "a":"ᔑ","b":"ʖ","c":"ᓵ","d":"↸","e":"ᒷ","f":"⎓","g":"⊣",
    "h":"⍑","i":"╎","j":"⋮","k":"ꖌ","l":"ꖎ","m":"ᒲ","n":"リ",
    "o":"𝙹","p":"!¡","q":"ᑑ","r":"∷","s":"ᓭ","t":"ℸ","u":"⚍",
    "v":"⍊","w":"∴","x":" ̇/","y":"||","z":"⨅"
}

def to_enchanting(text):
    return "".join(sga_map.get(c, c) for c in text.lower())


# 🔥 Summarization function
def summarize_text(text, lang="en", length="medium"):

    # Length control
    if length == "short":
        detail = "in 3-4 very short bullet points"
    elif length == "medium":
        detail = "in 6-8 clear bullet points"
    else:
        detail = "in 10-15 detailed bullet points"

    # Language control
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
    - No introduction
    - Start each point with "- "

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


# 🟢 Health check route
@app.get("/")
def home():
    return {"message": "API is working"}


# 🔥 Main summarization endpoint (frontend sends transcript)
@app.post("/summarize-text")
def summarize_text_api(data: dict = Body(...)):
    try:
        text = data.get("text")
        lang = data.get("lang", "en")
        length = data.get("length", "medium")

        if not text:
            return {"error": "No transcript text provided"}

        summary = summarize_text(text, lang, length)

        # 🎮 Minecraft conversion (after summary)
        if lang == "minecraft":
            summary = to_enchanting(summary)

        return {"summary": summary}

    except Exception as e:
        print("ERROR:", e)
        return {"error": "Something went wrong"}