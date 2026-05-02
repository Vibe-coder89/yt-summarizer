import { useState, useEffect } from "react";
import "./App.css";
import jsPDF from "jspdf";

function App() {
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState("en");
  const [length, setLength] = useState("medium");
  const [title, setTitle] = useState("");
  const [darkMode, setDarkMode] = useState(true);

  // Theme load
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved) setDarkMode(saved === "dark");
  }, []);

  useEffect(() => {
    document.body.className = darkMode ? "dark" : "light";
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const extractVideoId = (url) => {
    if (url.includes("v=")) return url.split("v=")[1].split("&")[0];
    if (url.includes("youtu.be/")) return url.split("youtu.be/")[1].split("?")[0];
    return url;
  };

  // 🔥 FIXED TRANSCRIPT FETCH (WITH PROXY)
  const fetchTranscript = async (videoId) => {
    try {
      const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(
        `https://www.youtube.com/api/timedtext?lang=en&v=${videoId}`
      )}`;

      const res = await fetch(proxyUrl);
      const xml = await res.text();

      if (!xml || xml.trim() === "") return null;

      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xml, "text/xml");

      const texts = Array.from(xmlDoc.getElementsByTagName("text"));

      return texts.map((t) => t.textContent).join(" ");
    } catch (err) {
      console.error(err);
      return null;
    }
  };

  const handleSummarize = async () => {
    if (!url) return;

    setLoading(true);
    setSummary("");

    try {
      const videoId = extractVideoId(url);

      // Get title
      try {
        const res = await fetch(
          `https://www.youtube.com/oembed?url=${url}&format=json`
        );
        const data = await res.json();
        setTitle(data.title);
      } catch {
        setTitle("youtube-summary");
      }

      // 🔥 Get transcript
      const transcriptText = await fetchTranscript(videoId);

      if (!transcriptText) {
        setSummary(
          "❌ No captions found.\nTry educational videos or TED talks."
        );
        setLoading(false);
        return;
      }

      // 🔥 Send to backend
      const response = await fetch(
        "https://yt-summarizer-1-4j2v.onrender.com/summarize-text",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: transcriptText,
            lang,
            length,
          }),
        }
      );

      const data = await response.json();

      if (data.summary) {
        setSummary(data.summary);
      } else {
        setSummary("Error: " + data.error);
      }
    } catch (err) {
      console.error(err);
      setSummary("❌ Something went wrong");
    }

    setLoading(false);
  };

  // PDF
  const downloadPDF = () => {
    if (!summary) return;

    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text(title || "YouTube Summary", 10, 10);

    doc.setFontSize(12);
    const lines = doc.splitTextToSize(summary, 180);

    let y = 20;
    lines.forEach((line) => {
      if (y > 280) {
        doc.addPage();
        y = 10;
      }
      doc.text(line, 10, y);
      y += 7;
    });

    doc.save((title || "summary") + ".pdf");
  };

  return (
    <div className="App">
      <div className="container">

        {/* Theme toggle */}
        <div className="toggle">
          <button onClick={() => setDarkMode(!darkMode)}>
            {darkMode ? "☀️" : "🌙"}
          </button>
        </div>

        <h1>🎥 YouTube Summarizer</h1>

        <input
          type="text"
          placeholder="Paste YouTube URL..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="harappan">Harappan</option>
          <option value="minecraft">Minecraft</option>
        </select>

        <div className="row">
          <select value={length} onChange={(e) => setLength(e.target.value)}>
            <option value="short">Short</option>
            <option value="medium">Medium</option>
            <option value="long">In-depth</option>
          </select>

          <button onClick={handleSummarize}>Summarize</button>
        </div>

        {loading && <p className="loading">⏳ Generating summary...</p>}

        {summary && (
          <>
            <div className="result">{summary}</div>

            <button onClick={downloadPDF} className="download-btn">
              📄 Download PDF
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;