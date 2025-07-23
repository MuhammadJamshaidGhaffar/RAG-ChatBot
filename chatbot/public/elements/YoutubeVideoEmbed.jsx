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
const YoutubeVideoEmbed = ({ 
}) => {

url = props.url;
const width = props.width || "80%"; // Responsive width for chat
const height = props.height || "45%"; // Responsive height for chat
const rel = props.rel || false;
const autoplay = props.autoplay || false;


  // Extract video ID from YouTube URL
  const getVideoId = (url) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  };

  const videoId = getVideoId(url);

  if (!videoId) {
    return <div>Invalid YouTube URL</div>;
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
