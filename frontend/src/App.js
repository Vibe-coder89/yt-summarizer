import { useState, useEffect } from "react";
import "./App.css";
import jsPDF from "jspdf";

// 🔥 use environment variable
const API_URL =
  process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function App() {
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState("en");
  const [length, setLength] = useState("medium");
  const [title, setTitle] = useState("");
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      setDarkMode(savedTheme === "dark");
    }
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.body.className = "dark";
      localStorage.setItem("theme", "dark");
    } else {
      document.body.className = "light";
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const handleSummarize = async () => {
    if (!url) return;

    setLoading(true);
    setSummary("");

    try {
      // 🎥 Get video title
      try {
        const res = await fetch(
          `https://www.youtube.com/oembed?url=${url}&format=json`
        );
        const data = await res.json();
        setTitle(data.title);
      } catch {
        setTitle("youtube-summary");
      }

      // 🔥 Use API URL (important change)
      const response = await fetch(
        `${API_URL}/summarize?url=${url}&lang=${lang}&length=${length}`
      );

      const data = await response.json();

      if (data.summary) {
        setSummary(data.summary);
      } else if (data.error) {
        setSummary("Error: " + data.error);
      } else {
        setSummary("Something went wrong");
      }
    } catch {
      setSummary("Error connecting to backend");
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