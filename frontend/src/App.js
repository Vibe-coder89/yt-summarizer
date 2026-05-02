import { useState } from "react";
import "./App.css";
import { YoutubeTranscript } from "youtube-transcript";

function App() {
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

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

      // 🔥 FETCH TRANSCRIPT FROM BROWSER
      const transcriptData = await YoutubeTranscript.fetchTranscript(videoId);

      const transcriptText = transcriptData
        .map((item) => item.text)
        .join(" ");

      // 🔥 SEND TEXT TO BACKEND (NOT URL)
      const response = await fetch(
        `https://your-render-backend-url/summarize-text`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ text: transcriptText }),
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

  return (
    <div className="App">
      <div className="container">
        <h1>🎥 YouTube Summarizer</h1>

        <input
          type="text"
          placeholder="Paste YouTube URL..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <button onClick={handleSummarize}>Summarize</button>

        {loading && <p>⏳ Generating summary...</p>}

        {summary && <div className="result">{summary}</div>}
      </div>
    </div>
  );
}

export default App;