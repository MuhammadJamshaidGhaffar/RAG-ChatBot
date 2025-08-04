// Function to modify chat input layout
function modifyChatInputLayout() {
  // Find the message composer container
  const messageComposer = document.querySelector("#message-composer");
  if (!messageComposer) {
    return;
  }

  // Find the chat input and submit button
  const chatInput = document.querySelector("#chat-input");
  const submitButton = document.querySelector("#chat-submit");

  if (!chatInput || !submitButton) {
    return;
  }

  // Check if we've already modified the layout
  if (messageComposer.querySelector(".chat-input-wrapper")) {
    return;
  }

  // Store references to the original parent elements
  const inputParent = chatInput.parentElement;
  const buttonParent = submitButton.parentElement;

  // Create wrapper for the new layout
  const chatInputWrapper = document.createElement("div");
  chatInputWrapper.className =
    "chat-input-wrapper flex items-center gap-3 w-full";

  // Create input container that will hold the original input
  const inputContainer = document.createElement("div");
  inputContainer.className = "flex-1 relative";

  // Create button container that will hold the original button
  const buttonContainer = document.createElement("div");
  buttonContainer.className = "flex-shrink-0";

  // Move the original elements (preserving all event listeners)
  inputContainer.appendChild(chatInput);
  buttonContainer.appendChild(submitButton);

  // Add containers to wrapper
  chatInputWrapper.appendChild(inputContainer);
  chatInputWrapper.appendChild(buttonContainer);

  // Clear the message composer and add our new structure
  messageComposer.innerHTML = "";
  messageComposer.appendChild(chatInputWrapper);

  console.log("Chat input layout modified successfully");
}

// Function to hide "Built with Chainlit" text
function hideBuiltWithChainlit() {
  // Target the specific watermark element
  const watermarkElements = document.querySelectorAll(
    'a.watermark, a[href*="chainlit.io"]'
  );

  watermarkElements.forEach((element) => {
    element.style.display = "none";
  });

  // More comprehensive hiding using multiple selectors
  const chainlitSelectors = [
    "a.watermark",
    'a[href*="chainlit.io"]',
    'a[target="_blank"]:has(div:contains("Built with"))',
    ".watermark",
    'div:contains("Built with") + svg',
    'div.text-xs:contains("Built with")',
  ];

  chainlitSelectors.forEach((selector) => {
    try {
      const elements = document.querySelectorAll(selector);
      elements.forEach((el) => {
        if (
          el.textContent.includes("Built with") ||
          el.href?.includes("chainlit.io")
        ) {
          el.style.display = "none";
        }
      });
    } catch (e) {
      // Ignore selector errors for unsupported selectors
    }
  });

  // Enhanced mutation observer specifically for watermark elements
  const watermarkObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Check for watermark class or chainlit.io href
          if (
            node.classList?.contains("watermark") ||
            node.href?.includes("chainlit.io")
          ) {
            node.style.display = "none";
          }

          // Check children for watermark elements
          const watermarks = node.querySelectorAll
            ? node.querySelectorAll('a.watermark, a[href*="chainlit.io"]')
            : [];
          watermarks.forEach((watermark) => {
            watermark.style.display = "none";
          });

          // Check for "Built with" text in any new elements
          if (
            node.textContent &&
            node.textContent.includes("Built with") &&
            node.textContent.includes("Chainlit")
          ) {
            node.style.display = "none";
          }

          // Check children for "Built with" text
          const chainlitElements = node.querySelectorAll
            ? node.querySelectorAll("*")
            : [];
          chainlitElements.forEach((el) => {
            if (
              el.textContent &&
              el.textContent.includes("Built with") &&
              el.textContent.includes("Chainlit")
            ) {
              el.style.display = "none";
            }
          });
        }
      });
    });
  });

  watermarkObserver.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

// Function to add dir="auto" to all elements with role="article"
function addDirAutoToArticles() {
  const articleElements = document.querySelectorAll('[role="article"]');
  articleElements.forEach((element) => {
    element.setAttribute("dir", "auto");
  });
}

// Function to replace overflow-auto with overflow-hidden in specific div
function replaceOverflowClass() {
  // Target the specific parent div with data-panel-group-id=":rc:"
  const parentPanel = document.querySelector('[data-panel-group-id=":rc:"]');

  if (parentPanel) {
    // Look for the specific child div within this exact parent
    const targetDiv = parentPanel.querySelector(
      ".flex.flex-row.flex-grow.overflow-auto"
    );

    if (targetDiv) {
      // Remove overflow-auto and add overflow-hidden
      targetDiv.classList.remove("overflow-auto");
      targetDiv.classList.add("overflow-hidden");
      console.log(
        "Successfully replaced overflow-auto with overflow-hidden in:",
        targetDiv
      );
      console.log("Parent container:", targetDiv.parentElement);
    } else {
      console.log(
        "Target child div with overflow-auto not found in the specified parent"
      );
    }
  } else {
    console.log("Parent div with data-panel-group-id=':rc:' not found");
  }
}

// Function to clone new chat button with all event listeners
function cloneNewChatButton() {
  // FIRST: Find the header parent div with id="header"
  const headerDiv = document.querySelector("#header");

  if (!headerDiv) {
    console.log("Header div with id='header' not found");
    return null;
  }

  console.log("Found header div:", headerDiv);

  // THEN: Find the new chat button within the header
  const originalButton = headerDiv.querySelector("#new-chat-button");

  if (!originalButton) {
    console.log("Original new chat button not found within header");
    return null;
  }

  // Find the parent div that contains the button - this is where the event listeners likely are
  const buttonContainer = originalButton.closest(".flex.items-center");

  if (!buttonContainer) {
    console.log("Button container div not found within header");
    return null;
  }

  console.log(
    "Found original button container within header:",
    buttonContainer
  );
  console.log("Container HTML:", buttonContainer.outerHTML);

  // Clone the ENTIRE container with deep cloning to preserve ALL structure and event listeners
  const clonedContainer = buttonContainer.cloneNode(true);

  // Find the button within the cloned container
  const clonedButton = clonedContainer.querySelector("button");

  if (clonedButton) {
    // Update the ID to avoid conflicts
    clonedButton.id = "header-new-chat-button";
    clonedButton.setAttribute("data-cloned", "true");

    // Add event listener to reload the page when clicked
    clonedButton.addEventListener("click", function (e) {
      console.log("Cloned new chat button clicked - reloading page...");
      // Small delay to allow any other handlers to complete
      setTimeout(() => {
        window.location.reload();
      }, 100);
    });
  }

  // Add identifier to the container
  clonedContainer.setAttribute("data-cloned-container", "true");

  console.log(
    "New chat button container cloned successfully from header with all event listeners preserved"
  );
  console.log("Cloned container HTML:", clonedContainer.outerHTML);

  return clonedContainer; // Return the entire container, not just the button
}

// Function to add FUE-style footer strip after input
function addFUEFooter() {
  // Check if our footer strip already exists
  if (document.querySelector(".fue-bottom-strip")) {
    return;
  }

  // Find the message composer container
  const messageComposer = document.querySelector("#message-composer");
  if (!messageComposer) {
    return;
  }

  // Find the parent container of message composer
  const parentContainer = messageComposer.parentElement;
  if (!parentContainer) {
    return;
  }

  // Create the bottom strip with red background
  const bottomStrip = document.createElement("div");
  bottomStrip.className = "fue-bottom-strip";
  bottomStrip.innerHTML = `
    <div class="strip-content">
      <!-- Contact details on the left -->
      <div class="strip-left">
        <div class="contact-info">
          <div class="phone-line">
            <span class="phone-symbol">📞</span>
            <span class="phone-number">16383</span>
          </div>
          <div class="website-line">
            <span class="website">www.fue.edu.eg</span>
          </div>
        </div>
      </div>
      
      <!-- Logo on the right -->
      <div class="strip-right">
        <img src="/public/branding-logo.png" alt="FUE Logo" class="strip-brand-logo" onerror="this.style.display='none'">
      </div>
    </div>
  `;

  // Insert the strip after the message composer
  parentContainer.insertBefore(bottomStrip, messageComposer.nextSibling);

  console.log("FUE bottom strip added successfully");
}

// Function to add FUE-style header to replace the existing header
function addFUEHeader() {
  // Check if our header already exists
  if (document.querySelector(".fue-custom-header")) {
    return;
  }

  // Find the existing header
  const existingHeader = document.querySelector("#header");
  if (!existingHeader) {
    return;
  }

  // FIRST: Clone the new chat button BEFORE replacing the header
  const originalButton = document.querySelector("#new-chat-button");
  let clonedButtonContainer = null;

  if (originalButton) {
    console.log("Cloning button container before header replacement...");
    clonedButtonContainer = cloneNewChatButton(); // This now returns the container
    console.log("Button container cloned successfully:", clonedButtonContainer);
  } else {
    console.log("Original new chat button not found before header replacement");
  }

  // Create the new FUE-style header
  const fueHeader = document.createElement("nav");
  fueHeader.className = "navbar navbar-expand-lg navbar-dark fue-custom-header";

  fueHeader.innerHTML = `
    <div class="container-fluid">
      <div class="header-layout">
        <!-- Logo and cloned button on the left -->
        <div class="header-left">
          <div id="new-chat-container" class="header-button-container"></div>
          <img src="/public/fue-white-logo.png" alt="Ask Nour Logo" class="brand-logo" onerror="this.style.display='none'">
        </div>
        
        <!-- Ask Nour text in the middle -->
        <div class="header-center">
          <div class="brand-title">Ask Nour</div>
          <div class="brand-subtitle">FUE Knowledge Companion</div>
        </div>
        
        <!-- Register button on the right -->
        <div class="header-right">
          <button class="btn btn-fue-white btn-sm" onclick="window.open('https://bit.ly/fue_asknour', '_blank')">
            <i class="bi bi-person-plus"></i> Register
          </button>
        </div>
      </div>
    </div>
  `;

  // Replace the existing header
  existingHeader.parentNode.replaceChild(fueHeader, existingHeader);

  // THEN: Add the cloned button container to the new header immediately
  if (clonedButtonContainer) {
    const buttonContainer = document.querySelector("#new-chat-container");
    if (buttonContainer) {
      buttonContainer.appendChild(clonedButtonContainer);
      console.log("Cloned new chat button container added to new header");
      console.log("Button container content:", buttonContainer.innerHTML);
    } else {
      console.log("Button container not found in new header");
    }
  }

  console.log("FUE header added successfully");
}

// Function to add required CSS styles for the header
function addFUEHeaderStyles() {
  if (!document.querySelector("#fue-header-styles")) {
    const style = document.createElement("style");
    style.id = "fue-header-styles";
    style.textContent = `
      /* FUE Brand Colors */
      :root {
        --fue-burgundy: #AE0F0A;
        --fue-burgundy-hover: #8B0C08;
        --fue-burgundy-dark: #8B0C08;
        --fue-burgundy-light: #D4130D;
        --fue-white: #FFFFFF;
        --fue-light-gray: #F8F9FA;
        --fue-gray: #6C757D;
        --fue-dark-gray: #495057;
        --fue-shadow-md: 0 4px 8px rgba(174, 15, 10, 0.15);
        --fue-radius-lg: 12px;
        --fue-font-weight-bold: 700;
        --fue-font-weight-medium: 500;
      }

      /* Header/Navbar Styling */
      .fue-custom-header {
        background: linear-gradient(90deg, var(--fue-burgundy) 0%, var(--fue-burgundy-dark) 100%) !important;
        backdrop-filter: blur(10px);
        box-shadow: var(--fue-shadow-md);
        border-bottom: 2px solid var(--fue-white);
        position: sticky;
        top: 0;
        z-index: 1000;
        padding: 0.4rem 0;
      }

      .fue-custom-header .container-fluid {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
      }

      /* Three-column header layout */
      .header-layout {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr;
        align-items: center;
        gap: 0.75rem;
        width: 100%;
      }

      /* Left section - Logo and cloned button */
      .header-left {
        justify-self: start;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }

      .brand-logo {
        height: 35px;
        object-fit: cover;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
      }

      /* Center section - Brand text */
      .header-center {
        justify-self: center;
        text-align: center;
      }

      .brand-title {
        font-size: 1.1rem;
        font-weight: var(--fue-font-weight-bold);
        margin: 0;
        color: var(--fue-white);
        line-height: 1.1;
      }

      .brand-subtitle {
        font-size: 0.75rem;
        opacity: 0.9;
        margin: 0;
        color: var(--fue-white);
        line-height: 1.1;
      }

      /* Right section - Button */
      .header-right {
        justify-self: end;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }

      /* Header button container for cloned buttons */
      .header-button-container {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      /* Styling for cloned new chat button in header */
      #header-new-chat-button {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: var(--fue-white) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
        padding: 6px 8px !important;
        font-size: 0.875rem !important;
      }

      #header-new-chat-button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-1px) !important;
      }

      #header-new-chat-button svg,
      #header-new-chat-button * {
        color: var(--fue-white) !important;
        fill: var(--fue-white) !important;
      }

      /* Navbar text */
      .fue-custom-header .navbar-text {
        color: var(--fue-white) !important;
        font-weight: var(--fue-font-weight-medium);
      }

      /* Button Styling */
      .btn-fue-white {
        background: var(--fue-white);
        border: none;
        color: var(--fue-burgundy);
        padding: 6px 12px;
        border-radius: 4px;
        transition: all 0.3s ease;
        font-weight: var(--fue-font-weight-bold);
        font-size: 0.8rem;
        box-shadow: 0 1px 3px rgba(174, 15, 10, 0.1);
      }

      .btn-fue-white:hover {
        background: var(--fue-light-gray);
        color: var(--fue-burgundy);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(174, 15, 10, 0.15);
      }

      /* Responsive design */
      @media (max-width: 768px) {
        .header-layout {
          grid-template-columns: auto 1fr auto;
          gap: 0.4rem;
        }

        .brand-subtitle {
          display: none;
        }
        
        .brand-title {
          font-size: 0.9rem;
        }
        
        .navbar-text {
          display: none !important;
        }

        .fue-custom-header .container-fluid {
          padding: 0 0.5rem;
        }

        .brand-logo {
          height: 28px;
          width: 28px;
        }

        .btn-fue-white {
          padding: 4px 8px;
          font-size: 0.7rem;
        }

        #header-new-chat-button {
          width: 32px !important;
          height: 32px !important;
        }
      }

      @media (max-width: 576px) {
        .header-layout {
          grid-template-columns: auto 1fr auto;
          gap: 0.2rem;
        }

        .brand-title {
          font-size: 0.8rem;
        }
        
        .brand-subtitle {
          font-size: 0.65rem;
        }

        .btn-fue-white {
          padding: 4px 6px;
          font-size: 0.65rem;
        }

        .brand-logo {
          height: 25px;
          width: 25px;
        }

        #header-new-chat-button {
          width: 28px !important;
          height: 28px !important;
        }

        .header-button-container {
          gap: 0.25rem;
        }
      }

      /* Ensure Bootstrap Icons work */
      @import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css');

      /* Bottom strip styling - positioned after input */
      .fue-bottom-strip {
        background: linear-gradient(90deg, var(--fue-burgundy) 0%, var(--fue-burgundy-dark) 100%);
        border-top: 2px solid var(--fue-burgundy-dark);
        padding: 0 1rem;
        width: 100vw;
        box-shadow: var(--fue-shadow-md);
        z-index: 100;
        transform: translateY(15px);
      }

      .strip-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        gap: 1rem;
      }

      .strip-left {
        display: flex;
        align-items: center;
      }

      .strip-left .contact-info {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        text-align: left;
      }

      .strip-left .phone-line {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .strip-left .phone-symbol {
        font-size: 1.1rem;
        color: var(--fue-white);
      }

      .strip-left .phone-number {
        font-size: 0.95rem;
        font-weight: var(--fue-font-weight-bold);
        color: var(--fue-white);
        letter-spacing: 0.5px;
      }

      .strip-left .website-line {
        display: flex;
      }

      .strip-left .website {
        font-size: 0.8rem;
        color: var(--fue-white);
        opacity: 0.9;
        font-weight: 500;
      }

      .strip-right {
        display: flex;
        align-items: center;
        justify-content: flex-end;
      }

      .strip-brand-logo {
        height: 45px;
        width: auto;
        max-width: 200px;
        object-fit: contain;
      }

      /* Hide strip on small screens to avoid overcrowding */
      @media (max-width: 768px) {
        .fue-bottom-strip {
          padding: 0 0.75rem;
        }
        
        .strip-left .phone-number {
          font-size: 0.85rem;
        }
        
        .strip-left .website {
          font-size: 0.75rem;
        }
        
        .strip-brand-logo {
          height: 35px;
          max-width: 150px;
        }
      }

      @media (max-width: 576px) {
        .fue-bottom-strip {
          display: none;
        }
      }

      /* Enhanced chat input layout */
      #message-composer {
        background: var(--fue-light-gray) !important;
        border: 2px solid var(--fue-burgundy) !important;
        border-radius: 25px !important;
        padding: 0.5rem 0.75rem !important;
        min-height: auto !important;
        height: auto !important;
        max-height: 60px !important;
      }

      .chat-input-wrapper {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        width: 100% !important;
        min-height: 40px !important;
        height: auto !important;
      }

      .chat-input-wrapper .flex-1 {
        flex: 1 !important;
        display: flex !important;
        align-items: center !important;
      }

      .chat-input-wrapper .flex-shrink-0 {
        flex-shrink: 0 !important;
        display: flex !important;
        align-items: center !important;
      }

      #chat-input {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0.5rem !important;
        font-size: 1rem !important;
        width: 100% !important;
        min-height: 40px !important;
        height: 40px !important;
        max-height: 40px !important;
        line-height: 1.4 !important;
        resize: none !important;
        overflow-y: hidden !important;
      }

      #chat-input:focus {
        outline: none !important;
        box-shadow: none !important;
      }

      /* Override any existing textarea styles */
      #chat-input[type="textarea"],
      textarea#chat-input {
        height: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
        resize: none !important;
        overflow-y: hidden !important;
      }

      #chat-submit {
        background: var(--fue-burgundy) !important;
        color: var(--fue-white) !important;
        border-radius: 50% !important;
        transition: all 0.3s ease !important;
        height: 36px !important;
        width: 36px !important;
        min-height: 36px !important;
        min-width: 36px !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 0 !important;
      }

      #chat-submit:hover {
        background: var(--fue-burgundy-hover) !important;
        transform: translateY(-1px) !important;
      }

      #chat-submit:disabled {
        background: var(--fue-gray) !important;
        opacity: 0.6 !important;
      }

      /* Ensure the parent container doesn't have extra height */
      #message-composer .chat-input-wrapper * {
        box-sizing: border-box !important;
      }

      /* Hide Built with Chainlit text and watermark */
      .watermark,
      a.watermark,
      a[href*="chainlit.io"],
      div[title*="Chainlit"],
      div:has(> span:contains("Built with")),
      .text-xs:contains("Built with") {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
      }

      /* Additional watermark hiding */
      a[target="_blank"][href="https://chainlit.io"] {
        display: none !important;
      }
    `;
    document.head.appendChild(style);
  }
}

// Function to handle register modal (you can customize this)
function showRegisterModal() {
  // Create a simple modal or redirect to registration
  const modal = document.createElement("div");
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  `;

  modal.innerHTML = `
    <div style="background: white; padding: 2rem; border-radius: 12px; max-width: 400px; width: 90%;">
      <h3 style="color: #AE0F0A; margin-bottom: 1rem;">Register for Ask Nour</h3>
      <p style="color: #495057; margin-bottom: 2rem;">Get access to enhanced features and personalized AI assistance.</p>
      <div style="display: flex; gap: 1rem; justify-content: flex-end;">
        <button onclick="this.closest('[style*=\"position: fixed\"]').remove()" 
                style="padding: 8px 16px; border: 1px solid #ccc; background: white; border-radius: 6px; cursor: pointer;">
          Cancel
        </button>
        <button onclick="window.open('/register', '_blank'); this.closest('[style*=\"position: fixed\"]').remove()" 
                style="padding: 8px 16px; background: #AE0F0A; color: white; border: none; border-radius: 6px; cursor: pointer;">
          Register Now
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

// Function to add Ask Nour branding to header (legacy function - now replaced by addFUEHeader)
function addAskNourBranding() {
  // This function is now replaced by addFUEHeader for better integration
  addFUEHeader();
}

// Function to add custom styles for branding (legacy - replaced by addFUEHeaderStyles)
// function addBrandingStyles() {
//   if (!document.querySelector("#ask-nour-header-styles")) {
//     const style = document.createElement("style");
//     style.id = "ask-nour-header-styles";
//     style.textContent = `
//       .ask-nour-branding {
//         transition: opacity 0.3s ease;
//       }
//
//       .ask-nour-branding:hover {
//         opacity: 0.8;
//       }
//
//       /* Make branding more prominent */
//       .ask-nour-branding span {
//         white-space: nowrap;
//       }
//
//       /* Responsive adjustments */
//       @media (max-width: 768px) {
//         .ask-nour-branding .text-xs {
//           display: none;
//         }
//       }
//
//       /* Theme-aware colors */
//       .dark .ask-nour-branding .text-primary {
//         color: hsl(var(--primary));
//       }
//     `;
//     document.head.appendChild(style);
//   }
// }

// Main initialization function
function initializeAskNourCustomizations() {
  addDirAutoToArticles();
  replaceOverflowClass();
  addFUEHeaderStyles();
  addFUEHeader();
  addFUEFooter();
  hideBuiltWithChainlit();

  // Delay chat input modification to ensure elements are loaded
  setTimeout(() => {
    modifyChatInputLayout();
    replaceOverflowClass(); // Run again after delay
  }, 500);

  // Run hideBuiltWithChainlit periodically to catch late-loading elements
  setInterval(() => {
    hideBuiltWithChainlit();
  }, 1000);
}

// Run the function when DOM is loaded
document.addEventListener("DOMContentLoaded", initializeAskNourCustomizations);

// Also run when new content is dynamically added
const observer = new MutationObserver((mutations) => {
  let shouldUpdateHeader = false;
  let shouldUpdateFooter = false;
  let shouldUpdateChatLayout = false;

  mutations.forEach((mutation) => {
    if (mutation.type === "childList") {
      // Check if header was added or modified
      const addedNodes = Array.from(mutation.addedNodes);
      if (
        addedNodes.some(
          (node) =>
            node.nodeType === Node.ELEMENT_NODE &&
            (node.id === "header" || node.querySelector("#header")) &&
            !node.classList.contains("fue-custom-header")
        )
      ) {
        shouldUpdateHeader = true;
      }

      // Check if the page content is loaded and bottom strip doesn't exist
      if (
        addedNodes.some(
          (node) =>
            node.nodeType === Node.ELEMENT_NODE &&
            (node.classList.contains("relative") ||
              node.querySelector(".relative") ||
              node.id === "message-composer" ||
              node.querySelector("#message-composer"))
        ) &&
        !document.querySelector(".fue-bottom-strip")
      ) {
        shouldUpdateFooter = true;
      }

      // Check if chat input components were added
      if (
        addedNodes.some(
          (node) =>
            node.nodeType === Node.ELEMENT_NODE &&
            (node.id === "message-composer" ||
              node.querySelector("#message-composer") ||
              node.id === "chat-input" ||
              node.querySelector("#chat-input"))
        )
      ) {
        shouldUpdateChatLayout = true;
      }
    }
  });

  if (shouldUpdateHeader) {
    setTimeout(() => {
      addFUEHeader();
    }, 100);
  }

  if (shouldUpdateFooter) {
    setTimeout(() => {
      addFUEFooter();
    }, 100);
  }

  if (shouldUpdateChatLayout) {
    setTimeout(() => {
      modifyChatInputLayout();
      hideBuiltWithChainlit();
      replaceOverflowClass(); // Also check for overflow class replacement

      // Try to add cloned new chat button if header exists but button is missing
      const buttonContainer = document.querySelector("#new-chat-container");
      const existingClonedButton = document.querySelector(
        "#header-new-chat-button"
      );
      const originalButton = document.querySelector("#new-chat-button");

      console.log("Mutation observer check:", {
        buttonContainer: !!buttonContainer,
        existingClonedButton: !!existingClonedButton,
        originalButton: !!originalButton,
      });

      if (buttonContainer && !existingClonedButton && originalButton) {
        const clonedButtonContainer = cloneNewChatButton();
        if (clonedButtonContainer) {
          buttonContainer.appendChild(clonedButtonContainer);
          console.log(
            "Cloned new chat button container added to header via mutation observer"
          );
        }
      }
    }, 200);
  }

  addDirAutoToArticles();
  replaceOverflowClass(); // Run on every mutation to catch new elements
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});
