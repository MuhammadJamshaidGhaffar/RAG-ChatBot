import React from "react";

/**
 * YoutubeVideoEmbed
 * Props:
 *   - url: string (YouTube video URL)
 *   - width: string (optional, default: "100%")
 *   - height: string (optional, default: "56.25%" for 16:9 aspect ratio)
 *   - rel: boolean (optional, show related videos, default: false)
 *   - autoplay: boolean (optional, default: false)
 */
const YoutubeVideoEmbed = () => {
  const { url, width = "80%", height = "45%", rel = false, autoplay = false } = props;

  print(`DEBUG: ============ YoutubeVideoEmbed Props ============`);
  print(`DEBUG: YouTube URL: ${url}, Width: ${width}, Height: ${height}, Rel: ${rel}, Autoplay: ${autoplay}`);

  // Extract video ID from YouTube URL
  const getVideoId = (url) => {
    // Check if url is valid
    if (!url || typeof url !== 'string') {
      return null;
    }
    
    // Multiple regex patterns to handle different YouTube URL formats
    const patterns = [
      // youtu.be format
      /(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})/,
      // youtube.com/watch format
      /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/,
      // youtube.com/embed format
      /(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
      // General fallback pattern
      /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        // For the first 3 patterns, video ID is in match[1]
        if (match[1] && match[1].length === 11) {
          return match[1];
        }
        // For the fallback pattern, video ID is in match[2]
        if (match[2] && match[2].length === 11) {
          return match[2];
        }
      }
    }
    
    return null;
  };

  const videoId = getVideoId(url);

  if (!url) {
    return <div style={{ padding: "10px", color: "#666" }}>No YouTube URL provided</div>;
  }

  if (!videoId) {
    return <div style={{ padding: "10px", color: "#666" }}>Invalid YouTube URL: {url}</div>;
  }

  // Build embed URL with parameters
  const embedUrl = `https://www.youtube.com/embed/${videoId}?rel=${rel ? 1 : 0}${autoplay ? '&autoplay=1' : ''}`;

  return (
    <div 
      style={{ 
        width: width,
        height: 0,
        position: "relative", 
        paddingBottom: "45%", // 16:9 aspect ratio (9/16 = 0.5625, but 45% for smaller size)
        margin: "10px auto",
        maxWidth: "400px" // Maximum size constraint
      }}
    >
      <iframe
        src={embedUrl}
        style={{
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          position: "absolute",
          border: 0,
          borderRadius: "8px"
        }}
        allowFullScreen
        scrolling="no"
        allow="accelerometer *; clipboard-write *; encrypted-media *; gyroscope *; picture-in-picture *; web-share *;"
        title="YouTube Video"
      />
    </div>
  );
};

export default YoutubeVideoEmbed;
