# src/codexes/pages/6_Pilsa_Bookstore.py
# version 1.3.4
import streamlit as st
import pandas as pd
import stripe
import os
import yaml
import json
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from datetime import datetime
import uuid
import bcrypt
import secrets
import string
import dotenv
import sys
from pathlib import Path

sys.path.insert(0, '/Users/fred/xcu_my_apps')

from dotenv import load_dotenv

load_dotenv()

# --- Helper function to get CLI arguments ---
def get_cli_arg(arg_name, default_value=None):
    """
    Parses sys.argv for a specific argument.
    Example usage: streamlit run storefront.py -- --catalog-file data/my_books.csv
    """
    args = sys.argv
    try:
        # Skip script name, and optional '--' separator used by Streamlit
        start_index = 1
        if len(args) > 1 and args[1] == '--':
            start_index = 2

        full_arg_list = args[start_index:]

        if arg_name in full_arg_list:
            index = full_arg_list.index(arg_name)
            if index + 1 < len(full_arg_list):
                return full_arg_list[index + 1]
            else:
                st.warning(f"CLI argument {arg_name} found but no value provided. Using default.")
                return default_value
        return default_value
    except Exception as e:
        st.error(f"Error parsing CLI arguments: {e}")
        return default_value

# --- Get catalog file path from imprint ---
if 'imprint' in st.session_state and st.session_state.get("imprint", "default"):
    catalog_file_path = Path('imprints') / st.session_state.get("imprint", "default") / 'books.csv'
else:
    catalog_file_path = Path("data/books.csv") # Fallback to default

# Configure Stripe API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "your_stripe_secret_key_here")

# Load and validate user configuration from YAML
try:
    # Ensure the config directory and file exist, or handle gracefully
    config_path = Path("resources/yaml/config.yaml")
    if not config_path.exists():
        st.error(f"{config_path} not found. Please ensure it exists.")
        st.stop()
    with open(config_path, "r") as file:
        config = yaml.load(file, Loader=SafeLoader)
    if not config or "credentials" not in config or "cookie" not in config:
        raise ValueError("Invalid config.yaml: missing 'credentials' or 'cookie' keys")
except FileNotFoundError:  # Should be caught by the explicit check above, but good to keep
    st.error(f"{config_path} not found. Please ensure it's in the 'resources/yaml/' directory relative to the script.")
    st.stop()
except Exception as e:
    st.error(f"Error loading config.yaml: {e}")
    st.stop()

# Translation dictionary
translations = {
    "en": {
        "select_language": "Select Language",
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "login_button": "Login",
        "no_account": "Don't have an account? Sign up below:",
        "signup": "Sign Up",
        "create_account": "Create Account",
        "email": "Email",
        "name": "Name",
        "register_success": "User {username} registered successfully! Your password is {password}. Please save it securely.",
        "login_error": "Username/password is incorrect",
        "login_warning": "Please enter your username and password",
        "registration_error": "Error during registration: {error}",
        "welcome": "Welcome, {name}!",
        "logout": "Logout",
        "logout_success": "Logged out successfully.",
        "please_login": "Please log in to complete your purchase.",
        "login_to_checkout": "Please login or create an account to proceed with checkout",
        "catalog": "Catalog",
        "by": "by",
        "view_details": "View Details",
        "author": "Author",
        "description": "Description",
        "price": "Price",
        "add_to_cart": "Add to Cart",
        "pre_order": "Pre-Order Now",
        "back_to_catalog": "Back to Catalog",
        "added_to_cart": "Added to cart!",
        "cart": "Shopping Cart",
        "empty_cart": "Your cart is empty.",
        "total": "Total",
        "proceed_checkout": "Proceed to Checkout",
        "redirect_stripe": "Redirecting to Stripe Checkout...",
        "complete_payment": "Complete Payment",
        "checkout_error": "Error creating checkout session: {error}",
        "payment_success": "Payment successful! Your order has been placed.",
        "payment_canceled": "Payment canceled.",
        "account_created": "Account created! Username: {username}, Password: {password}. Please save these credentials securely.",
        "cart_items": "Cart ({count})",
        "details_header": "Book Details",
        "page_count": "Page Count",
        "trim_size": "Trim Size",
        "interior_color": "Interior",
        "binding": "Binding",
        "keywords": "Bibliographic Keywords",
        "toc": "Table of Contents",
        "bisac_codes": "BISAC Codes",
        "publication_date": "Publication Date",
        "download_pdf_sample": "Download PDF Sample",
        "front_cover": "Front Cover",
        "back_cover": "Back Cover",
        "full_spread": "Full Cover Spread",
        "back_cover_text_header": "From the Back Cover",
        "books_listed": "books listed"
    },
    "ko": {
        "select_language": "언어 선택",
        "login": "로그인",
        "username": "사용자 이름",
        "password": "비밀번호",
        "login_button": "로그인",
        "no_account": "���정이 없으신가요? 아래에서 가입하세요:",
        "signup": "가입",
        "create_account": "계정 만들기",
        "email": "이메일",
        "name": "이름",
        "register_success": "{username} 사용자가 성공적으로 등록되었습니다! 비밀번호는 {password}입니다. 안전하게 저장해 주세요.",
        "login_error": "사용자 이름/비밀번호가 올바르지 않습니다.",
        "login_warning": "사용자 이름과 비밀번호를 입력해 주세요.",
        "registration_error": "등록 중 오류 발생: {error}",
        "welcome": "{name}님, 환영합니다!",
        "logout": "로그아웃",
        "logout_success": "성공적으로 로그아웃되었습니다.",
        "please_login": "구매를 완료하려면 로그인해 주세요.",
        "login_to_checkout": "결제를 진행하려면 로그인하거나 계정을 만드세요.",
        "catalog": "책 카탈로그",
        "by": "저자",
        "view_details": "Buy now",
        "author": "저자",
        "description": "설명",
        "price": "가격",
        "add_to_cart": "장바구니에 추가",
        "pre_order": "지금 예약 주문",
        "back_to_catalog": "카탈로그로 돌아가기",
        "added_to_cart": "장바구니에 추가되었습니다!",
        "cart": "장바구니",
        "empty_cart": "장바구니가 비어 있습니다.",
        "total": "총액",
        "proceed_checkout": "결제 진행",
        "redirect_stripe": "Stripe 결제로 리디렉션 중...",
        "complete_payment": "결제 완료",
        "checkout_error": "결제 세션 생성 오류: {error}",
        "payment_success": "결제 성공! 주문이 완료되었습니다.",
        "payment_canceled": "결제가 취소되었습니다.",
        "account_created": "계정이 생성되었습니다! 사용자 이름: {username}, 비밀번호: {password}. 이 자격 증명을 안전하게 저장해 주세요.",
        "cart_items": "장바구니 ({count})",
        "details_header": "도서 정보",
        "page_count": "페이지 수",
        "trim_size": "판형",
        "interior_color": "���지 색상",
        "binding": "제본 방식",
        "keywords": "키워드",
        "toc": "목차",
        "bisac_codes": "BISAC 코드",
        "publication_date": "발행일",
        "download_pdf_sample": "PDF 샘플 다운로드",
        "front_cover": "앞표지",
        "back_cover": "뒷표지",
        "full_spread": "전체 표지",
        "back_cover_text_header": "뒷표지 내용",
        "books_listed": "권이 목록에 나타납니다."
    }
}

# --- Load or create book catalog ---
try:
    catalog_file_path.parent.mkdir(parents=True, exist_ok=True)

    if catalog_file_path.exists() and catalog_file_path.stat().st_size > 0:
        books_df = pd.read_csv(catalog_file_path)
        st.toast(f"Loaded catalog from: {catalog_file_path}")
        # ensure id is type str
        if 'id' in books_df.columns:
            books_df['id'] = books_df['id'].astype(str)
        # Ensure required author columns exist, add them with defaults if not
        if 'author_en' not in books_df.columns:
            books_df['author_en'] = "Unknown Author"
        if 'author_ko' not in books_df.columns:
            books_df['author_ko'] = "알 수 없는 저자"
    else:
        st.warning(f"Catalog file '{catalog_file_path}' not found or empty. Creating default catalog.")
        books_data = {
            "id": [1, 2, 3],
            "title_en": ["The Great Novel", "History of Time", "Poetry Collection"],
            "title_ko": ["위대한 소설", "시간의 역사", "시 모음집"],
            "author_en": ["Jane Doe", "John Smith", "Emily Brown"],  # Changed from author
            "author_ko": ["제인 도", "존 스미스", "에밀리 브라운"],  # Added Korean authors
            "description_en": [
                "An epic tale of adventure and discovery.",
                "A journey through the ages.",
                "A collection of heartfelt poems."
            ],
            "description_ko": [
                "모험과 발견의 서사시.",
                "시대를 통한 여정.",
                "진심이 담긴 시 모음."
            ],
            "price": [29.99, 24.99, 19.99],
            "image_url": [
                "https://via.placeholder.com/150/0000FF/FFFFFF?Text=Book1",
                "https://via.placeholder.com/150/FF0000/FFFFFF?Text=Book2",
                "https://via.placeholder.com/150/00FF00/FFFFFF?Text=Book3"
            ]
        }
        books_df = pd.DataFrame(books_data)
        books_df.to_csv(catalog_file_path, index=False)
        st.info(f"Default catalog created and saved to: {catalog_file_path}")

except pd.errors.EmptyDataError:
    st.error(f"Catalog file '{catalog_file_path}' is empty. Please check the file or provide a valid one.")
    st.stop()
except Exception as e:
    st.error(f"Error loading or creating catalog file '{catalog_file_path}': {e}")
    st.stop()

# Initialize session state
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "page" not in st.session_state:
    st.session_state.page = "catalog"
if "username" not in st.session_state:
    st.session_state.username = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "stripe_session_id" not in st.session_state:
    st.session_state.stripe_session_id = None

# Language selector
def get_translation(lang, key, **kwargs):
    try:
        return translations[lang][key].format(**kwargs) if kwargs else translations[lang][key]
    except KeyError:
        # Fallback to English if translation is missing for the current language
        if lang != "en" and key in translations.get("en", {}):
            return translations["en"][key].format(**kwargs) if kwargs else translations["en"][key]
        return f"[{key}_MISSING_IN_{lang.upper()}]"

# Helper function to get translated book field
def get_book_field(row, field_base_name, lang):
    """
    Retrieves a field from the book data row in the specified language.
    Falls back to English if the language-specific field doesn't exist or if lang is 'en'.
    Example: field_base_name='title' will try 'title_ko' then 'title_en'.
             field_base_name='author' will try 'author_ko' then 'author_en'.
    """
    lang_specific_col = f"{field_base_name}_{lang}"
    english_col = f"{field_base_name}_en"

    if lang != "en" and lang_specific_col in row and pd.notna(row[lang_specific_col]):
        return row[lang_specific_col]
    elif english_col in row and pd.notna(row[english_col]):  # Fallback to English
        return row[english_col]
    # Fallback if even English field is missing or NaN
    return f"[{field_base_name.upper()}_INFO_MISSING]"

# Helper function to get cart key
def get_cart_key():
    return st.session_state.username if st.session_state.username else st.session_state.session_id

# Helper function to get cart item count
def get_cart_count():
    cart_key = get_cart_key()
    return len(st.session_state.cart.get(cart_key, []))

# Helper function to generate random password
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

# Helper function to create user account
def create_user_account(email):
    try:
        email_prefix = email.split("@")[0].replace(".", "_").lower()
        random_suffix = secrets.token_hex(4)
        username = f"{email_prefix}_{random_suffix}"
        password = generate_password()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        config["credentials"]["usernames"][username] = {
            "email": email,
            "name": email_prefix.replace("_", " ").title(),
            "password": hashed_password
        }
        # Ensure config_path is defined and accessible here, or pass it
        with open(Path("resources/yaml/config.yaml"), "w") as file:
            yaml.dump(config, file, default_flow_style=False)

        st.session_state.username = username
        transfer_cart_to_user(username)
        return username, password
    except Exception as e:
        st.error(f"Error creating user account: {e}")
        return None, None

# Helper function to transfer cart to user
def transfer_cart_to_user(username):
    if st.session_state.session_id in st.session_state.cart:
        if username not in st.session_state.cart:
            st.session_state.cart[username] = []
        st.session_state.cart[username].extend(st.session_state.cart[st.session_state.session_id])
        del st.session_state.cart[st.session_state.session_id]

# Function to display authentication forms
def display_auth_forms():
    st.subheader(get_translation(st.session_state.language, "login"))

    # Login form
    with st.form("login_form"):
        username = st.text_input(get_translation(st.session_state.language, "username"))
        password = st.text_input(get_translation(st.session_state.language, "password"), type="password")
        submit_login = st.form_submit_button(get_translation(st.session_state.language, "login_button"))

        if submit_login:
            if username and password:
                # Check credentials manually
                user_data = config["credentials"]["usernames"].get(username)
                if user_data and bcrypt.checkpw(password.encode("utf-8"), user_data["password"].encode("utf-8")):
                    st.session_state.username = username
                    transfer_cart_to_user(username)
                    st.session_state.page = "cart"
                    st.success(
                        get_translation(st.session_state.language, "welcome", name=user_data.get("name", username)))
                    st.rerun()
                else:
                    st.error(get_translation(st.session_state.language, "login_error"))
            else:
                st.warning(get_translation(st.session_state.language, "login_warning"))

    st.write(get_translation(st.session_state.language, "no_account"))

    # Registration form
    with st.form("register_form"):
        new_email = st.text_input(get_translation(st.session_state.language, "email"))
        new_username = st.text_input(f"{get_translation(st.session_state.language, 'username')} (for registration)")
        new_name = st.text_input(get_translation(st.session_state.language, "name"))
        new_password = st.text_input(f"{get_translation(st.session_state.language, 'password')} (for registration)",
                                     type="password")
        submit_register = st.form_submit_button(get_translation(st.session_state.language, "signup"))

        if submit_register:
            if new_email and new_username and new_name and new_password:
                # Check if username already exists
                if new_username in config["credentials"]["usernames"]:
                    st.error("Username already exists. Please choose a different username.")
                else:
                    try:
                        # Hash the password
                        hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

                        # Add new user to config
                        config["credentials"]["usernames"][new_username] = {
                            "email": new_email,
                            "name": new_name,
                            "password": hashed_password
                        }

                        # Save updated config
                        with open(Path("resources/yaml/config.yaml"), "w") as file:
                            yaml.dump(config, file, default_flow_style=False)

                        st.session_state.username = new_username
                        transfer_cart_to_user(new_username)
                        st.session_state.page = "cart"
                        st.success(get_translation(st.session_state.language, "register_success", username=new_username,
                                                   password="[your chosen password]"))
                        st.rerun()
                    except Exception as e:
                        st.error(get_translation(st.session_state.language, "registration_error", error=str(e)))
            else:
                st.warning("Please fill in all registration fields.")

# Function to display book catalog
def display_catalog():
    """Displays the book catalog in a vertical list format."""
    st.header(get_translation(st.session_state.language, "catalog"))

    # TO DO -- create books_df by loading multiple spreadsheets, list them concisely here instead of catalog_file_path

    st.markdown(f"{imprint_intro} {len(books_df)} {get_translation(st.session_state.language, 'books_listed')} from {catalog_file_path}")

    if books_df.empty:
        st.warning("Book catalog is empty. Please check the catalog file.")
        return

    # Inject custom CSS for the new vertical list layout
    st.markdown("""
        <style>
        /* Thumbnail image styling */
        .stImage img {
            width: 150px !important;
            height: auto !important;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        /* Vivid Korean traditional color separators */
        .separator-1 {
            border: 0;
            height: 3px; /* Thicker line */
            background-image: linear-gradient(to right, rgba(77, 168, 255, 0.8), rgba(138, 109, 255, 0.8)); /* Blue to Purple */
            margin: 1.5rem 0;
        }
        .separator-2 {
            border: 0;
            height: 3px; /* Thicker line */
            background-image: linear-gradient(to right, rgba(255, 102, 102, 0.8), rgba(255, 215, 0, 0.8)); /* Red to Gold */
            margin: 1.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Loop through each book and display it in a vertical list format
    for idx, row in books_df.iterrows():
        col1, col2 = st.columns([1, 3])  # 1 part for image, 3 for text

        with col1:
            if "front_cover_image_path" in row and pd.notna(row["front_cover_image_path"]):
                st.image(str(row["front_cover_image_path"]), use_container_width=False)
            else:
                # Display a placeholder if no cover image is available
                st.image("https://via.placeholder.com/150x225/CCCCCC/FFFFFF?Text=No+Cover", use_container_width=False)

        with col2:
            title = row.get('title', 'Unknown Title')
            author = row.get('author', 'Unknown Author')
            description = get_book_field(row, 'storefront_publishers_note', st.session_state.language)
            price = row.get('price', 0.00)
            pub_date_str = row.get('publication_date', None)
            lang = st.session_state.language

            st.subheader(title)
            st.markdown(f"_{get_translation(lang, 'by')} {author}_")

            if pub_date_str:
                st.caption(f"{get_translation(lang, 'publication_date')}: {pub_date_str}")

            st.caption(description)
            st.markdown(f"**{get_translation(lang, 'price')}:** ${price:.2f}")

            # --- Action Buttons ---
            btn_col1, btn_col2, btn_col3 = st.columns(3)

            with btn_col1:
                # Add to Cart / Pre-Order Button logic
                button_label = get_translation(lang, "add_to_cart")
                if 'publication_date' in row and pd.notna(row['publication_date']):
                    try:
                        pub_date = datetime.strptime(str(row['publication_date']), '%Y-%m-%d').date()
                        if pub_date > datetime.today().date():
                            button_label = get_translation(lang, "pre_order")
                    except (ValueError, TypeError):
                        pass

                book_id = row.get('id')
                if st.button(button_label, key=f"add_to_cart_catalog_{idx}", use_container_width=True):
                    if book_id and str(book_id) != 'nan':
                        # Add item to cart (session or user)
                        cart_key = get_cart_key()
                        if cart_key not in st.session_state.cart:
                            st.session_state.cart[cart_key] = []
                        st.session_state.cart[cart_key].append({
                            "book_id": book_id,
                            "title": row.get('title', 'Unknown Title'),
                            "price": row.get('price', 0.00)
                        })
                        st.toast(get_translation(lang, "added_to_cart"))

                        # If not logged in, redirect to auth page to secure the cart
                        if not st.session_state.username:
                            st.session_state.page = "auth"
                            st.rerun()
                    else:
                        st.warning("Cannot add to cart (missing a unique ID).")

            with btn_col2:
                # Amazon link button
                if 'amazon_url' in row and pd.notna(row['amazon_url']) and row['amazon_url']:
                    st.link_button("Buy on Amazon", row['amazon_url'], use_container_width=True)

            with btn_col3:
                # View Details button
                book_id = row.get('id')
                button_key = f"view_details_{idx}"  # Use index to guarantee uniqueness
                if st.button(get_translation(lang, "view_details"), key=button_key, use_container_width=True):
                    if book_id and str(book_id) != 'nan':
                        st.session_state.page = f"details_{book_id}"
                        st.rerun()
                    else:
                        st.warning("Book details are not available for this entry (missing a unique ID).")

        # Add a styled horizontal rule, alternating colors
        separator_class = "separator-1" if idx % 2 == 0 else "separator-2"
        st.markdown(f"<hr class='{separator_class}'>", unsafe_allow_html=True)

def display_book_details(book_id):
    """Displays a detailed page for a single book."""
    book_row = books_df[books_df['id'] == str(book_id)]
    if book_row.empty:
        st.error("Book not found.")
        if st.button(get_translation(st.session_state.language, "back_to_catalog")):
            st.session_state.page = "catalog"
            st.rerun()
        return

    book = book_row.iloc[0]
    lang = st.session_state.language

    # FIX: Use .get() for non-translated fields like title and author.
    title = book.get('title', 'Unknown Title')
    author = book.get('author', 'Unknown Author')
    st.header(title)
    st.subheader(f"{get_translation(lang, 'by')} {author}")
    st.markdown("---")

    col1, col2 = st.columns([2, 3])

    with col1:
        # --- Image Carousel ---
        image_list = []
        caption_list = []
        if 'front_cover_image_path' in book and pd.notna(book['front_cover_image_path']):
            image_list.append(book['front_cover_image_path'])
            caption_list.append(get_translation(lang, 'front_cover'))
        if 'back_cover_image_path' in book and pd.notna(book['back_cover_image_path']):
            image_list.append(book['back_cover_image_path'])
            caption_list.append(get_translation(lang, 'back_cover'))
        if 'full_spread_image_path' in book and pd.notna(book['full_spread_image_path']):
            image_list.append(book['full_spread_image_path'])
            caption_list.append(get_translation(lang, 'full_spread'))

        # FIX: Use st.tabs to create a carousel-like image viewer.
        if image_list:
            tabs = st.tabs(caption_list)
            for i, tab in enumerate(tabs):
                with tab:
                    st.image(image_list[i], use_container_width=True)
        else:
            st.image("https://via.placeholder.com/400x600/CCCCCC/FFFFFF?Text=No+Image", use_container_width=True)

        # --- PDF Sample Link ---
        if 'PDF sample' in book and pd.notna(book['PDF sample']):
            st.link_button(get_translation(lang, "download_pdf_sample"), book['PDF sample'], use_container_width=True)

        # --- Amazon Link ---
        if 'amazon_url' in book and pd.notna(book['amazon_url']) and book['amazon_url']:
            st.link_button("🛒 Buy on Amazon", book['amazon_url'], use_container_width=True, type="secondary")

    with col2:
        st.subheader(get_translation(lang, "details_header"))

        publishers_note = get_book_field(book, 'storefront_publishers_note', lang)
        if publishers_note and "MISSING" not in publishers_note:
            st.markdown(publishers_note)
            st.markdown("---")

        details_map = {
            "page_count": get_translation(lang, "page_count"),
            "publication_date": get_translation(lang, "publication_date"),
        }
        for key, label in details_map.items():
            if key in book and pd.notna(book[key]):
                st.markdown(f"**{label}:** {book[key]}")

        back_cover_text = get_book_field(book, 'back_cover_text', lang)
        if back_cover_text and "MISSING" not in back_cover_text:
            with st.expander(get_translation(lang, "back_cover_text_header")):
                st.markdown(back_cover_text)

        # --- Add to Cart / Pre-Order Button (Moved to the bottom) ---
        st.markdown("---")  # Visual separator
        button_label = get_translation(lang, "add_to_cart")
        if 'publication_date' in book and pd.notna(book['publication_date']):
            try:
                pub_date = datetime.strptime(str(book['publication_date']), '%Y-%m-%d').date()
                if pub_date > datetime.today().date():
                    button_label = get_translation(lang, "pre_order")
            except (ValueError, TypeError):
                pass  # Ignore malformed dates

        if st.button(button_label, key=f"add_to_cart_{book_id}", use_container_width=True, type="primary"):
            # Add item to cart (session or user)
            cart_key = get_cart_key()
            if cart_key not in st.session_state.cart:
                st.session_state.cart[cart_key] = []
            st.session_state.cart[cart_key].append({
                "book_id": book_id,
                "title": book.get('title', 'Unknown Title'),
                "price": book.get('price', 0.00)
            })
            st.toast(get_translation(lang, "added_to_cart"))

            # If not logged in, redirect to auth page to secure the cart.
            # Otherwise, the rerun will just update the cart icon.
            if not st.session_state.username:
                st.session_state.page = "auth"

            st.rerun()

    if st.button(get_translation(lang, "back_to_catalog")):
        st.session_state.page = "catalog"
        st.rerun()

# Function to display cart and handle checkout
def display_cart():
    st.header(get_translation(st.session_state.language, "cart"))
    cart_key = get_cart_key()
    user_cart = st.session_state.cart.get(cart_key, [])

    if not user_cart:
        st.write(get_translation(st.session_state.language, "empty_cart"))
        if st.button(get_translation(st.session_state.language, "back_to_catalog"),
                     key="back_to_catalog_empty_cart"):
            st.session_state.page = "catalog"
            st.rerun()
        return

    total = 0
    for item_idx, item in enumerate(user_cart):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{item['title']}**")
            st.write(f"{get_translation(st.session_state.language, 'price')}: ${item['price']:.2f}")
        with col2:
            if st.button("Remove", key=f"remove_item_{cart_key}_{item_idx}_{item.get('book_id', 'unknown')}"):
                st.session_state.cart[cart_key].pop(item_idx)
                st.rerun()
        st.markdown("---")  # Separator
        total += item["price"]

    st.write(f"**{get_translation(st.session_state.language, 'total')}**: ${total:.2f}")

    # Check if user is logged in before allowing checkout
    if not st.session_state.username:
        st.info(get_translation(st.session_state.language, "login_to_checkout"))
        col1, col2 = st.columns(2)
        with col1:
            if st.button(get_translation(st.session_state.language, "login"),
                         key="login_from_cart"):
                st.session_state.page = "auth"
                st.rerun()
        with col2:
            if st.button(get_translation(st.session_state.language, "create_account"),
                         key="create_account_from_cart"):
                st.session_state.page = "auth"
                st.rerun()

        if st.button(get_translation(st.session_state.language, "back_to_catalog"),
                     key="back_to_catalog_from_cart"):
            st.session_state.page = "catalog"
            st.rerun()
    else:
        # User is logged in, allow checkout
        if st.button(get_translation(st.session_state.language, "proceed_checkout"),
                     key="proceed_to_checkout"):
            try:
                line_items = [{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": item["title"]
                        },
                        "unit_amount": int(item["price"] * 100),
                    },
                    "quantity": 1
                } for item in user_cart]

                base_url = os.getenv("STREAMLIT_SERVER_BASE_URL", "http://localhost:8501")
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=line_items,
                    mode="payment",
                    success_url=f"{base_url}?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{base_url}?success=false",
                    metadata={"session_id": st.session_state.session_id,
                              "username": st.session_state.username or "guest"}
                )
                st.session_state.stripe_session_id = session.id
                st.markdown(f"[{get_translation(st.session_state.language, 'complete_payment')}]({session.url})")
            except Exception as e:
                st.error(get_translation(st.session_state.language, "checkout_error", error=e))

        if st.button(get_translation(st.session_state.language, "back_to_catalog"),
                     key="back_to_catalog_after_checkout"):
            st.session_state.page = "catalog"
            st.rerun()

# Main app logic
st.set_page_config(page_title="Bookstore", layout="wide")

# Load imprint-specific data
imprint_title = "Bookstore"
imprint_intro = ""
if st.session_state.get("imprint"):
    try:
        imprint_config_path = Path("imprints") / st.session_state.get("imprint", "default") / "prompts.json"
        with open(imprint_config_path, "r", encoding="utf-8") as f:
            imprint_config = json.load(f)
            # Assuming title and intro are in the prompts file for now
            imprint_title = imprint_config.get("imprint_name", st.session_state.get("imprint", "default").replace("_", " ").title())
            imprint_intro = imprint_config.get("pilsa_intro", "Welcome to our bookstore!") # Still uses pilsa_intro key

    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Could not load config for '{st.session_state.get('imprint', 'default')}': {e}")

st.title(imprint_title)

# --- Header with Cart and Auth ---
header_cols = st.columns([3, 1, 1])
with header_cols[1]:
    # Always show cart button with item count
    cart_count = get_cart_count()
    cart_label = get_translation(st.session_state.language, "cart_items",
                                 count=cart_count) if cart_count > 0 else get_translation(st.session_state.language, "cart")
    if st.button(cart_label, key="header_cart_button", use_container_width=True):
        st.session_state.page = "cart"
        st.rerun()

with header_cols[2]:
    # Authentication section
    if not st.session_state.username:
        if st.button(get_translation(st.session_state.language, "login"), key="header_login_button", use_container_width=True):
            st.session_state.page = "auth"
            st.rerun()
    else:
        if st.button(get_translation(st.session_state.language, "logout"), key="header_logout_button", use_container_width=True):
            st.session_state.username = None
            st.session_state.page = "catalog"
            st.session_state.session_id = str(uuid.uuid4())
            st.success(get_translation(st.session_state.language, "logout_success"))
            st.rerun()
st.markdown("---")

# Handle success/cancel from Stripe
query_params = st.query_params
if "success" in query_params:
    success_value = query_params.get("success")
    stripe_checkout_session_id = query_params.get("session_id")

    if success_value == "true":
        try:
            if stripe_checkout_session_id and stripe_checkout_session_id == st.session_state.stripe_session_id:
                session = stripe.checkout.Session.retrieve(stripe_checkout_session_id)
                email = session.customer_details.email if session.customer_details else None
                if email and not st.session_state.username:
                    username, password = create_user_account(email)
                    if username:
                        st.success(get_translation(
                            st.session_state.language, "account_created",
                            username=username, password=password
                        ))
                        st.session_state.username = username
                cart_key_after_payment = get_cart_key()
                if cart_key_after_payment in st.session_state.cart:
                    st.session_state.cart[cart_key_after_payment] = []
                st.session_state.stripe_session_id = None
                st.success(get_translation(st.session_state.language, "payment_success"))
            elif not stripe_checkout_session_id:
                st.warning("Stripe session ID missing from success URL. Cannot verify payment fully.")
            else:
                st.error("Stripe session ID mismatch. Payment verification failed.")
        except stripe.error.StripeError as e:
            st.error(f"Stripe API error processing payment: {e}")
        except Exception as e:
            st.error(f"Error processing payment: {e}")
    elif success_value == "false":
        st.error(get_translation(st.session_state.language, "payment_canceled"))

    st.query_params.clear()
    st.session_state.page = "catalog"  # Go to catalog after processing payment redirect
    st.rerun()

# Route to appropriate page
if st.session_state.page == "catalog":
    display_catalog()
elif st.session_state.page.startswith("details_"):
    try:
        book_id = st.session_state.page.split("_")[1]
        display_book_details(book_id)
    except (IndexError, ValueError):
        print("Invalid book details page.")
        st.session_state.page = "catalog"
        st.rerun()
elif st.session_state.page == "cart":
    display_cart()
elif st.session_state.page == "auth":
    display_auth_forms()
