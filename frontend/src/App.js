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

  // Theme
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved) setDarkMode(saved === "dark");
  }, []);

  useEffect(() => {
    document.body.className = darkMode ? "dark" : "light";
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const handleSummarize = async () => {
    if (!url) return;

    setLoading(true);
    setSummary("");

    try {
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

      // 🔥 Backend call
      const response = await fetch(
        `https://yt-summarizer-1-4j2v.onrender.com/summarize?url=${url}&lang=${lang}&length=${length}`
      );

      const data = await response.json();

      if (data.summary) {
        setSummary(data.summary);
      } else {
        setSummary("❌ " + data.error);
      }
    } catch (err) {
      console.error(err);
      setSummary("❌ Backend error");
    }

    setLoading(false);
  };

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

    doc.save(`${title || "summary"}.pdf`);
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
        </select>

        <div className="row">
          <select value={length} onChange={(e) => setLength(e.target.value)}>
            <option value="short">Short</option>
            <option value="medium">Medium</option>
            <option value="long">In-depth</option>
          </select>

          <button onClick={handleSummarize}>Summarize</button>
        </div>

        {loading && <p>⏳ Generating summary...</p>}

        {summary && (
          <>
            <div className="result">{summary}</div>

            <button onClick={downloadPDF}>
              📄 Download PDF
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;