# Chrome Extension Architecture for Social Xtuff Text-to-Post

## Overview

A Chrome extension that allows users to right-click on any selected text or webpage content and submit it directly to Social Xtuff AI personas for transformation into social media posts.

## Extension Structure

```
social-xtuff-extension/
├── manifest.json           # Extension configuration
├── background.js           # Background service worker
├── content.js             # Content script for page interaction
├── popup/
│   ├── popup.html         # Extension popup interface
│   ├── popup.js           # Popup logic
│   └── popup.css          # Popup styling
├── icons/
│   ├── icon16.png         # Extension icons
│   ├── icon48.png
│   └── icon128.png
└── options/
    ├── options.html       # Extension settings
    ├── options.js         # Settings logic
    └── options.css        # Settings styling
```

## Core Features

### 1. Context Menu Integration
- Right-click on selected text → "Send to Social Xtuff"
- Right-click on links → "Transform URL content"
- Right-click on page → "Send page content"

### 2. API Integration
- Connects to Social Xtuff API at `http://localhost:8502`
- Supports all available personas
- Handles URL auto-detection and preservation
- Real-time status updates

### 3. User Interface
- **Context Menu**: Quick access to transformation
- **Popup Interface**: Full persona selection and options
- **Settings Page**: Configure API endpoint, default persona, auto-submit preferences

### 4. Smart Content Detection
- Automatically extracts relevant text from web pages
- Preserves formatting and URLs
- Handles different content types (articles, social posts, etc.)

## Implementation Plan

### Phase 1: Basic Extension (MVP)
1. **Manifest v3 setup** with required permissions
2. **Context menu** for selected text
3. **Direct API calls** to Social Xtuff endpoint
4. **Simple popup** for persona selection
5. **Basic error handling**

### Phase 2: Enhanced Features
1. **Page content extraction** with smart text selection
2. **Settings page** for configuration
3. **Multiple API endpoints** support
4. **Response preview** before posting
5. **Offline queue** for failed requests

### Phase 3: Advanced Features
1. **Auto-posting** to multiple social platforms
2. **Content scheduling** capabilities
3. **Analytics dashboard** for generated content
4. **Custom persona creation** interface
5. **Collaborative features** for teams

## Technical Specifications

### Manifest.json
```json
{
  "manifest_version": 3,
  "name": "Social Xtuff Text Transformer",
  "version": "1.0.0",
  "description": "Transform any text into engaging social media content using AI personas",
  "permissions": [
    "contextMenus",
    "activeTab",
    "storage",
    "host_permissions"
  ],
  "host_permissions": [
    "http://localhost:8502/*",
    "https://your-api-domain.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

### API Communication
```javascript
class SocialXtuffAPI {
  constructor(baseURL = 'http://localhost:8502') {
    this.baseURL = baseURL;
  }

  async getPersonas() {
    const response = await fetch(`${this.baseURL}/personas`);
    return response.json();
  }

  async submitText(text, personaId, options = {}) {
    const response = await fetch(`${this.baseURL}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        persona_id: personaId,
        user_id: options.userId || 'chrome_extension',
        model_override: options.modelOverride,
        preserve_urls: options.preserveUrls !== false
      })
    });
    return response.json();
  }
}
```

### Context Menu Handler
```javascript
chrome.contextMenus.create({
  id: "social-xtuff-transform",
  title: "Transform with Social Xtuff",
  contexts: ["selection", "link", "page"]
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const text = info.selectionText || info.linkUrl || 'Current page content';
  // Open popup with pre-filled text
  chrome.action.openPopup();
});
```

## Security Considerations

1. **API Key Management**: Secure storage of user API credentials
2. **HTTPS Requirements**: Enforce secure connections in production
3. **Content Validation**: Sanitize user input before API calls
4. **Permission Scoping**: Minimal required permissions
5. **Data Privacy**: No persistent storage of user content

## User Experience Flow

1. **User selects text** on any webpage
2. **Right-clicks** and chooses "Send to Social Xtuff"
3. **Extension popup opens** with text pre-filled
4. **User selects persona** and any advanced options
5. **Click "Transform"** to send to API
6. **View generated content** in popup
7. **Copy to clipboard** or post directly to social platforms

## Configuration Options

### Extension Settings
- **Default API Endpoint**: localhost:8502 or custom URL
- **Default Persona**: User's preferred AI persona
- **Auto-submit**: Skip confirmation dialog
- **URL Preservation**: Always/never/ask
- **Content Length Limits**: Max characters to send

### Per-Request Options
- **Persona Selection**: Choose from available personas
- **Model Override**: Select specific AI model
- **URL Handling**: Preserve, strip, or transform URLs
- **Output Format**: Raw text, markdown, or formatted

## Development Setup

```bash
# Clone extension template
git clone https://github.com/your-org/social-xtuff-extension

# Install dependencies
npm install

# Build extension
npm run build

# Load in Chrome
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the build directory
```

## Testing Strategy

1. **Unit Tests**: Core API communication logic
2. **Integration Tests**: Full workflow with live API
3. **Cross-browser Testing**: Chrome, Firefox, Edge compatibility
4. **Performance Testing**: Large text handling, API timeouts
5. **User Testing**: Real-world usage scenarios

## Deployment

1. **Chrome Web Store**: Primary distribution channel
2. **Enterprise Distribution**: For corporate users
3. **Auto-updates**: Seamless version management
4. **Analytics**: Usage tracking and error reporting

## Future Enhancements

1. **Multi-platform Support**: Firefox, Safari, Edge
2. **Mobile App Integration**: Companion mobile app
3. **Social Platform APIs**: Direct posting to Twitter, LinkedIn, etc.
4. **Team Collaboration**: Shared persona libraries
5. **Content Analytics**: Performance tracking for generated posts