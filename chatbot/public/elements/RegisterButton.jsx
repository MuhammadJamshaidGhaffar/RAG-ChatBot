import React from 'react';


const RegisterButton = () => {

    // { url, text = "📝 Register My Application", description = "Click on the button to complete your university application" }
    
    const url = props.url || "https://bit.ly/fue_asknour";
    const text = props.text || "📝 Register My Application";
    const description = props.description || "Click on the button to complete your university application";

console.log(`DEBUG: ============ RegisterButton Props ============`);
console.log(`DEBUG : props : ${JSON.stringify(props)}`);

  const handleClick = () => {
    // Open the registration URL in a new tab
    console.log(`DEBUG: Opening registration URL: ${url}`);
    window.open(url, '_blank');
  };

return (
    <div style={{ margin: '16px 0' }}>
        <button
            onClick={handleClick}
            style={{
                backgroundColor: '#AE0F0A',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 24px',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 2px 4px rgba(174,15,10,0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                textDecoration: 'none',
                minWidth: '200px',
                justifyContent: 'center'
            }}
            onMouseOver={(e) => {
                e.target.style.backgroundColor = '#8B0C08';
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 4px 8px rgba(174,15,10,0.4)';
            }}
            onMouseOut={(e) => {
                e.target.style.backgroundColor = '#AE0F0A';
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 2px 4px rgba(174,15,10,0.3)';
            }}
            title={description}
        >
            {text}
        </button>
        <p style={{ 
            fontSize: '12px', 
            color: '#666', 
            margin: '8px 0 0 0',
            textAlign: 'center'
        }}>
            {description}
        </p>
    </div>
);
};

export default RegisterButton;
