# Integration Guide for Individual Apps

**Purpose:** Add consistent navigation back to the xtuff.ai dashboard from all individual applications

---

## Adding "Return to Dashboard" Button

Each individual app should include a "Return to xtuff.ai Dashboard" button at the top of its sidebar.

### Method 1: Copy the Widget File (Recommended)

1. **Copy the widget file to your app:**

```bash
cp /home/wfz/bin/all_applications_runner/resources/sidebar_widget.py /path/to/your/app/
```

2. **Import and use in your app:**

```python
import streamlit as st
from sidebar_widget import add_return_to_dashboard_button

# Set page config first
st.set_page_config(page_title="Your App", layout="wide")

# Add return button at the very top of your sidebar
add_return_to_dashboard_button()

# Rest of your sidebar content
st.sidebar.title("Your App")
# ... your sidebar code ...

# Main content
st.title("Your Application")
# ... your main app code ...
```

### Method 2: Inline Code (Quick & Simple)

Add this code at the top of your app (after page config, before other sidebar content):

```python
import streamlit as st

# At the very top of your script
st.set_page_config(page_title="Your App", layout="wide")

# Add return button
if st.sidebar.button("← Return to xtuff.ai Dashboard", type="secondary", use_container_width=True):
    st.markdown('<meta http-equiv="refresh" content="0; url=http://xtuff.ai">', unsafe_allow_html=True)
st.sidebar.markdown("---")

# Rest of your app...
```

### Method 3: Simple Link (Minimal)

For a lighter-weight alternative, use a text link:

```python
import streamlit as st

st.set_page_config(page_title="Your App", layout="wide")

# Add return link
st.sidebar.markdown("[← Back to Dashboard](http://xtuff.ai)")
st.sidebar.markdown("---")

# Rest of your app...
```

---

## Apps Configuration

### Apps Managed by all_applications_runner:

According to `apps_config.json`, these apps should be updated:

**xtuff.ai Apps:**
- Daily Engine (`/home/wfz/personal-time-management/daily_engine.py`)
- Social Xtuff (`/home/wfz/agentic_social_server/app.py`)
- Text-to-Feed API (`/home/wfz/agentic_social_server/api_server.py`)
- Collectiverse (`/home/wfz/collectiverse/app.py`)
- TrillionsOfPeople (`/home/wfz/trillionsofpeople/trillionsofpeople.py`)
- altDOGE (`/home/wfz/altDOGE/cfr_document_analyzer/streamlit_app.py`)

**Nimble Books Apps:**
- Codexes Factory (`/home/wfz/codexes-factory/src/codexes/codexes-factory-home-ui.py`)
- Max Bialystok (`/home/wfz/codexes-factory/max_bialystok_home.py`)

**Personal Apps:**
- Resume & Contact (`/home/wfz/resume-site/app.py`)

---

## Implementation Checklist

For each app:

- [ ] Copy `sidebar_widget.py` to the app directory OR add inline code
- [ ] Add the return button at the TOP of the sidebar (before other content)
- [ ] Test that clicking the button returns to http://xtuff.ai
- [ ] Ensure the button appears consistently across all pages (if multi-page app)

---

## Customization Options

### Change the Button Text

```python
add_return_to_dashboard_button(button_text="← Back to Main")
```

### Change the Dashboard URL

```python
add_return_to_dashboard_button(dashboard_url="https://xtuff.ai")
```

### Remove the Divider Line

```python
add_return_to_dashboard_button(show_divider=False)
```

### Button Styling

The button uses Streamlit's `type="secondary"` style. To customize further:

```python
# Custom styled button
import streamlit as st

st.sidebar.markdown("""
    <a href="http://xtuff.ai" style="text-decoration: none;">
        <button style="
            width: 100%;
            padding: 0.5rem;
            background-color: #0066cc;
            color: white;
            border: none;
            border-radius: 0.25rem;
            cursor: pointer;
            font-size: 14px;
        ">
            ← Return to xtuff.ai Dashboard
        </button>
    </a>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
```

---

## Multi-Page Apps

For Streamlit multi-page apps, add the button in one of these locations:

### Option 1: In Each Page File

Add to the top of each page file:

```python
# pages/1_Page_One.py
import streamlit as st
from sidebar_widget import add_return_to_dashboard_button

add_return_to_dashboard_button()

st.title("Page One")
# ... page content ...
```

### Option 2: In Main App File (Appears on All Pages)

If your main app file controls the sidebar:

```python
# main_app.py
import streamlit as st
from sidebar_widget import add_return_to_dashboard_button

st.set_page_config(page_title="My App", layout="wide")

# This will appear on all pages
add_return_to_dashboard_button()

# Navigation
page = st.navigation([...])
page.run()
```

---

## Testing

After implementing, verify:

1. **Button appears** at the top of the sidebar
2. **Button is clickable** and doesn't cause errors
3. **Clicking returns** to http://xtuff.ai (or configured URL)
4. **Consistent appearance** across all app pages
5. **No conflicts** with other sidebar elements

---

## Troubleshooting

### Button doesn't navigate

If using the button method, ensure `unsafe_allow_html=True` is enabled:

```python
st.markdown('<meta http-equiv="refresh" content="0; url=http://xtuff.ai">', unsafe_allow_html=True)
```

### Button appears in wrong location

Ensure the button code is:
- After `st.set_page_config()`
- Before any other sidebar content
- At the top of your script or page file

### Styling conflicts

If using custom CSS, ensure it doesn't override the button styles. Use `!important` if needed.

---

## Examples

### Example: Daily Engine

```python
# daily_engine.py
import streamlit as st
from sidebar_widget import add_return_to_dashboard_button

st.set_page_config(page_title="Daily Engine", layout="wide")

# Add return button first
add_return_to_dashboard_button()

# App sidebar content
st.sidebar.title("⚡ Daily Engine")
st.sidebar.write("Life automation system")

# Main app
st.title("Daily Engine")
# ... rest of app ...
```

### Example: Codexes Factory

```python
# codexes-factory-home-ui.py
import streamlit as st
import sys
from pathlib import Path

# Add resources path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from resources.sidebar_widget import add_return_to_dashboard_button

st.set_page_config(page_title="Codexes Factory", layout="wide")

# Add return button
add_return_to_dashboard_button()

# Rest of Codexes Factory app...
```

---

## File Locations

**Widget File:** `/home/wfz/bin/all_applications_runner/resources/sidebar_widget.py`

**This Guide:** `/home/wfz/bin/all_applications_runner/INTEGRATION_GUIDE.md`

---

**Last Updated:** 2025-10-03
