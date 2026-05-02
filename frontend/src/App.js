import { useState, useEffect } from "react";
import "./App.css";
import jsPDF from "jspdf";
import { YoutubeTranscript } from "youtube-transcript";

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
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      setDarkMode(savedTheme === "dark");
    }
  }, []);

  // Theme apply
  useEffect(() => {
    if (darkMode) {
      document.body.className = "dark";
      localStorage.setItem("theme", "dark");
    } else {
      document.body.className = "light";
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const extractVideoId = (url) => {
    if (url.includes("v=")) {
      return url.split("v=")[1].split("&")[0];
    } else if (url.includes("youtu.be/")) {
      return url.split("youtu.be/")[1].split("?")[0];
    }
    return url;
  };

  const handleSummarize = async () => {
    if (!url) return;

    setLoading(true);
    setSummary("");

    try {
      const videoId = extractVideoId(url);

      // Get video title
      try {
        const res = await fetch(
          `https://www.youtube.com/oembed?url=${url}&format=json`
        );
        const data = await res.json();
        setTitle(data.title);
      } catch {
        setTitle("youtube-summary");
      }

      // 🔥 Fetch transcript from browser
      const transcriptData = await YoutubeTranscript.fetchTranscript(videoId);

      const transcriptText = transcriptData
        .map((item) => item.text)
        .join(" ");

      // 🔥 Send to backend
      const response = await fetch(
        "https://yt-summarizer-1-4j2v.onrender.com",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: transcriptText,
            lang: lang,
            length: length,
          }),
        }
      );

      const data = await response.json();

      if (data.summary) {
        setSummary(data.summary);
      } else {
        setSummary("Error: " + data.error);
      }
    } catch (error) {
      console.error(error);
      setSummary("Could not fetch transcript for this video");
    }

    setLoading(false);
  };

  const downloadPDF = () => {
    if (!summary) return;

    const doc = new jsPDF();

    const pageHeight = doc.internal.pageSize.height;
    const margin = 10;
    const lineHeight = 7;

    doc.setFontSize(16);
    doc.text(title || "YouTube Summary", margin, margin);

    doc.setFontSize(12);

    const lines = doc.splitTextToSize(summary, 180);

    let y = 20;

    lines.forEach((line) => {
      if (y + lineHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }

      doc.text(line, margin, y);
      y += lineHeight;
    });

    const cleanTitle = (title || "youtube-summary").replace(
      /[\\/:*?"<>|]/g,
      ""
    );

    doc.save(`${cleanTitle}.pdf`);
  };

  return (
    <div className="App">
      <div className="container">

        {/* 🌙 Toggle */}
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