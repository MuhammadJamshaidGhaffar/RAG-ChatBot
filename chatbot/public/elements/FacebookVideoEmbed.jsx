import React from "react";

/**
 * FacebookVideoWidget
 * A simple, clean widget to display Facebook video links
 * Props:
 *   - url: string (Facebook video URL)
 *   - title: string (optional - video title)
 *   - description: string (optional - video description)
 *   - width: number (optional - widget width)
 */
const FacebookVideoEmbed = () => {

  const title = props.title;
  const url = props.url;
  const description = props.description || "";
  const width = props.width || 500; // Default width for the widget


  print(`DEBUG: ============ FacebookVideoEmbed Props ============`);
  print(`DEBUG: Facebook Video URL: ${url}, Width: ${width}, Title: ${title}, Description: ${description}`);

  const handleClick = () => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  // Extract a readable title from URL if no title provided
  const displayTitle = title || "Facebook Video";
  
  return (
    <div 
      style={{
        maxWidth: `${width}px`,
        border: '1px solid #e1e5e9',
        borderRadius: '8px',
        padding: '16px',
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
        fontFamily: 'Arial, sans-serif',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        margin: '8px 0'
      }}
      onClick={handleClick}
      onMouseEnter={(e) => {
        e.target.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.15)';
        e.target.style.transform = 'translateY(-1px)';
      }}
      onMouseLeave={(e) => {
        e.target.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        e.target.style.transform = 'translateY(0)';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
        <div 
          style={{
            width: '24px',
            height: '24px',
            backgroundColor: '#1877f2',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: '8px',
            flexShrink: 0
          }}
        >
          <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold' }}>f</span>
        </div>
        <span style={{ 
          fontSize: '12px', 
          color: '#65676b', 
          fontWeight: '600',
          letterSpacing: '0.5px'
        }}>
          FACEBOOK VIDEO
        </span>
      </div>
      
      <h3 style={{
        margin: '0 0 8px 0',
        fontSize: '16px',
        fontWeight: '600',
        color: '#1c1e21',
        lineHeight: '1.3',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical'
      }}>
        {displayTitle}
      </h3>
      
      {description && (
        <p style={{
          margin: '0 0 12px 0',
          fontSize: '14px',
          color: '#65676b',
          lineHeight: '1.4',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical'
        }}>
          {description}
        </p>
      )}
      
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '12px',
        paddingTop: '12px',
        borderTop: '1px solid #f0f2f5'
      }}>
        <span style={{
          fontSize: '12px',
          color: '#65676b',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          flex: 1,
          marginRight: '8px'
        }}>
          {url}
        </span>
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="#1877f2" 
          strokeWidth="2"
          style={{ flexShrink: 0 }}
        >
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
          <polyline points="15,3 21,3 21,9"></polyline>
          <line x1="10" y1="14" x2="21" y2="3"></line>
        </svg>
      </div>
    </div>
  );
};

export default FacebookVideoEmbed;
