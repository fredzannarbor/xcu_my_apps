# Shared UI Components for my-apps

Unified sidebar component for all applications in the my-apps workspace.

## Features

- **🔐 Authentication**: Login/Register/Subscribe (integrated with workspace auth)
- **🌐 xtuff.ai Navigation**: Quick links to all apps (collapsible)
- **📱 App Navigation**: Custom navigation for each app
- **ℹ️ Version Info**: Machine, git branch/commit/tag, Python version (collapsible)
- **📧 Contact Widget**: Substack subscription form + quick message (collapsible)

## Usage

### Basic Integration

```python
import streamlit as st

# Add to PYTHONPATH or install shared module
import sys
sys.path.insert(0, '/Users/fred/xcu_my_apps')

from shared.ui import render_unified_sidebar

# Render sidebar (usually at top of your app)
render_unified_sidebar(
    app_name="My Application",
    nav_items=[
        ("Home", "pages/home.py"),
        ("Settings", "pages/settings.py"),
    ]
)

# Your main page content goes here
st.title("Welcome to My App")
```

### Advanced Options

```python
render_unified_sidebar(
    app_name="My App",
    nav_items=[
        ("Dashboard", "pages/dashboard.py"),
        ("Analytics", "http://localhost:8503/analytics"),  # External link
    ],
    show_auth=True,           # Show login/register (default: True)
    show_xtuff_nav=True,      # Show xtuff.ai apps menu (default: True)
    show_version=True,        # Show version info (default: True)
    show_contact=True         # Show contact form (default: True)
)
```

## Best Practices

### ✅ DO:
- **Keep sidebar for navigation only** - No functional forms
- **Move forms to main page** - Put functional widgets in containers
- **Use collapsible sections** - All detail sections are collapsed by default
- **Provide app-specific nav** - Help users navigate within your app

### ❌ DON'T:
- **Don't duplicate info** - Auth/version/contact are handled centrally
- **Don't put forms in sidebar** - Move search, filters, inputs to main page
- **Don't hardcode URLs** - Use the unified component

## Example: Migrating an Existing App

**Before (redundant sidebar):**
```python
# ❌ Old way - redundant code in every app
st.sidebar.title("Login")
st.sidebar.text_input("Email")
st.sidebar.text_input("Password")
st.sidebar.button("Login")

st.sidebar.title("Navigation")
st.sidebar.page_link("pages/home.py", label="Home")

st.sidebar.title("Search")  # ❌ Functional form in sidebar
st.sidebar.text_input("Search query")
```

**After (unified sidebar):**
```python
# ✅ New way - clean and unified
from shared.ui import render_unified_sidebar

render_unified_sidebar(
    app_name="My App",
    nav_items=[("Home", "pages/home.py")]
)

# ✅ Move functional forms to main page
with st.container():
    st.subheader("Search")
    search_query = st.text_input("Search query")
```

## Authentication Integration

The sidebar uses `st.session_state` for auth:

```python
# Check if user is authenticated
if st.session_state.get('authenticated', False):
    st.success("Welcome back!")
else:
    st.info("Please login to continue")

# Get user email
user_email = st.session_state.get('user_email', 'guest@example.com')
```

## Component Structure

```
shared/
├── __init__.py
├── ui/
│   ├── __init__.py
│   └── unified_sidebar.py   # Main sidebar component
└── auth/                     # Future: centralized auth module
```

## Customization

To customize the sidebar for your app:

1. **Skip sections** you don't need:
   ```python
   render_unified_sidebar(
       app_name="Simple App",
       show_auth=False,      # No auth needed
       show_contact=False    # No contact form
   )
   ```

2. **Add custom sections** after the unified sidebar:
   ```python
   render_unified_sidebar(app_name="My App")

   # Add custom sidebar content
   st.sidebar.markdown("---")
   st.sidebar.markdown("### Custom Section")
   st.sidebar.info("App-specific info here")
   ```

## Future Enhancements

- [ ] Real authentication backend integration
- [ ] Stripe subscription integration
- [ ] User profile management
- [ ] Theme customization
- [ ] Analytics tracking
- [ ] Multi-language support
