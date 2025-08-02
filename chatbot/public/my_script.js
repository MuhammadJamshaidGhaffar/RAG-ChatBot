// Function to add dir="auto" to all elements with role="article"
function addDirAutoToArticles() {
  const articleElements = document.querySelectorAll('[role="article"]');
  articleElements.forEach((element) => {
    element.setAttribute("dir", "auto");
  });
}

// Function to add Ask Nour branding to header
function addAskNourBranding() {
  // Target the middle div in header using the absolute positioning classes
  const headerMiddleDiv = document.querySelector(
    "#header .absolute.top-1\\/2.left-1\\/2.-translate-x-1\\/2.-translate-y-1\\/2"
  );

  if (headerMiddleDiv && !headerMiddleDiv.querySelector(".ask-nour-branding")) {
    // Create branding container
    const brandingContainer = document.createElement("div");
    brandingContainer.className = "ask-nour-branding flex items-center gap-2";

    // Add logo (if you have one in public folder)
    const logoImg = document.createElement("img");
    logoImg.src = "/public/fue-red-logo.jpg";
    logoImg.alt = "Ask Nour Logo";
    logoImg.className = "h-8 w-8 rounded-full object-contain";
    logoImg.style.display = "none"; // Hide initially, show when loaded
    logoImg.onload = () => (logoImg.style.display = "block");
    logoImg.onerror = () => logoImg.remove(); // Remove if image fails to load

    // Add text branding
    const brandingText = document.createElement("div");
    brandingText.className = "flex flex-col items-center";
    brandingText.innerHTML = `
      <span class="text-sm font-semibold text-primary">Ask Nour</span>
      <span class="text-xs text-muted-foreground">FUE Assistant</span>
    `;

    // Assemble branding
    brandingContainer.appendChild(logoImg);
    brandingContainer.appendChild(brandingText);

    // Insert into header
    headerMiddleDiv.appendChild(brandingContainer);

    console.log("Ask Nour branding added to header");
  }
}

// Function to add custom styles for branding
function addBrandingStyles() {
  if (!document.querySelector("#ask-nour-header-styles")) {
    const style = document.createElement("style");
    style.id = "ask-nour-header-styles";
    style.textContent = `
      .ask-nour-branding {
        transition: opacity 0.3s ease;
      }
      
      .ask-nour-branding:hover {
        opacity: 0.8;
      }
      
      /* Make branding more prominent */
      .ask-nour-branding span {
        white-space: nowrap;
      }
      
      /* Responsive adjustments */
      @media (max-width: 768px) {
        .ask-nour-branding .text-xs {
          display: none;
        }
      }
      
      /* Theme-aware colors */
      .dark .ask-nour-branding .text-primary {
        color: hsl(var(--primary));
      }
    `;
    document.head.appendChild(style);
  }
}

// Main initialization function
function initializeAskNourCustomizations() {
  addDirAutoToArticles();
  addBrandingStyles();
  addAskNourBranding();
}

// Run the function when DOM is loaded
document.addEventListener("DOMContentLoaded", initializeAskNourCustomizations);

// Also run when new content is dynamically added
const observer = new MutationObserver((mutations) => {
  let shouldUpdate = false;

  mutations.forEach((mutation) => {
    if (mutation.type === "childList") {
      // Check if header was added or modified
      const addedNodes = Array.from(mutation.addedNodes);
      if (
        addedNodes.some(
          (node) =>
            node.nodeType === Node.ELEMENT_NODE &&
            (node.id === "header" || node.querySelector("#header"))
        )
      ) {
        shouldUpdate = true;
      }
    }
  });

  if (shouldUpdate) {
    setTimeout(() => {
      addAskNourBranding();
    }, 100);
  }

  addDirAutoToArticles();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});
