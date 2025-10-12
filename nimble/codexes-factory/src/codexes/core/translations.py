import streamlit as st
import logging

# Centralized dictionary for English and Korean translations.
translations = {
    "en": {
        "title": "Codexes Factory by Nimble Books",
        "nav_home": "Home",
        "nav_ideation": "Ideation & Development",
        "nav_enhancement": "Manuscript Enhancement",
        "nav_metadata": "Metadata & Distribution",
        "nav_settings": "Settings & Commerce",
        "nav_bookstore": "Bookstore",
        "nav_admin": "Admin Dashboard",

        "sidebar_header": "Codexes Factory",
        "sidebar_status": "**Status:** Operational",
        "version_info": "Version Information",
        "module_inventory_header": "Module Inventory",
        "module_inventory_help":
            "These are existing libraries to be integrated into this framework.",
        # Auth
        "login": "Log in",
        "logout": "Log out",
        "logout_button": "Log out",
        "username": "Username",
        "password": "Password",
        "login_button": "Login",
        "logout_success": "Logged out successfully.",
        "welcome": "Welcome *{name}*",
        "welcome_message": "Welcome *{name}* to the Codexes Factory. Navigation in sidebar.",
        "WELCOME_MESSAGE": "Welcome *{name}* to the Codexes Factory. Navigation in sidebar.",
        "please_login_or_register": "Please login or register.",
        "login_error": "Username/password is incorrect",
        "register_user": "Register user",
        "register_user_preauth": "Please contact us for pre-authorization",
        "register_success": "User {username}  recognized. Please log in.",
        "login_register_page_title": "Log In or Register",
        "nav_login": "Log In or Register",
        "already_logged_in": "Status: logged in",
        "user_role": "user role",
        "role_display": "Role: {role}",
        "ROLE_DISPLAY": "Role: {role}",
        "login_form_title": "Log In",
        'login_tab': "Log In",
        "register_tab": "Register",
        'not_logged_in': "Status: not logged in",
        'current_role': "User role",
        
        # Bookstore
        "select_language": "Language / 언어",
        "catalog": "Book Catalog",
        "by": "by",
        "view_details": "View Details",
        "author": "Author",
        "description": "Description",
        "price": "Price",
        "add_to_cart": "Add to Cart",
        "back_to_catalog": "Back to Catalog",
        "added_to_cart": "Added to cart!",
        "cart": "Shopping Cart",
        "empty_cart": "Your cart is empty.",
        "total": "Total",
        "proceed_checkout": "Proceed to Checkout",
        "redirect_stripe": "Redirecting to Stripe Checkout...",
        "complete_payment": "Click here to complete payment",
        "checkout_error": "Error creating checkout session: {error}",
        "payment_success": "Payment successful!",
        "payment_canceled": "Payment canceled.",
        "cart_items": "Cart ({count})",
        "details_header": "Book Details",
        "page_count": "Page Count",
        "trim_size": "Trim Size",
        "interior_color": "Interior",
        "binding": "Binding",
        "keywords": "Keywords",
        "toc": "Table of Contents",
        "bisac_codes": "BISAC Codes",
        "publication_date": "Publication Date",
        "login_to_checkout": "Please log in to proceed with checkout.",
    },
    "ko": {
        "title": "님블북스의 코덱세스",
        "nav_home": "홈",
        "nav_ideation": "아이디어 및 개발",
        "nav_enhancement": "원고 개선",
        "nav_metadata": "메타데이터 및 배포",
        "nav_settings": "설정 및 커머스",
        "nav_bookstore": "서점",
        "nav_admin": "관리자 대시보드",

        "sidebar_header": "코덱세스 AI",
        "sidebar_status": "**상태:** 운영 중",
        "version_info": "버전 정보",
        "module_inventory_header": "모듈 인벤토리",
        "module_inventory_help": "이 프레임워크에 통합될 기존 라이브러리입니다.",
        
        # Auth
        "login": "로그인",
        "logout": "로그아웃",
        "username": "사용자 이름",
        "password": "비밀번호",
        "login_button": "로그인",
        "logout_success": "성공적으로 로그아웃되었습니다.",
        "welcome": "*__{name}__님, 환영합니다*",
        "welcome_message": "*{name}*님, 코덱세스 팩토리에 오신 것을 환영합니다. 사이드바에서 탐색하세요.",
        "WELCOME_MESSAGE": "*{name}*님, 코덱세스 팩토리에 오신 것을 환영합니다. 사이드바에서 탐색하세요.",
        "role_display": "역할: {role}",
        "ROLE_DISPLAY": "역할: {role}",
        "please_login_or_register": "로그인 또는 가입해주세요.",
        "login_error": "사용자 이름 또는 비밀번호가 잘못되었습니다.",
        "register_user": "사용자 등록",
        "register_user_preauth": "사전 승인을 위해 문의해 주세요",
        "register_success": "사용자 등록 성공! 로그인해주세요.",

        # Bookstore
        "select_language": "언어 선택 / Language",
        "catalog": "도서 카탈로그",
        "by": "저자",
        "view_details": "자세히 보기",
        "author": "저자",
        "description": "설명",
        "price": "가격",
        "add_to_cart": "장바구니에 추가",
        "back_to_catalog": "카탈로그로 돌아가기",
        "added_to_cart": "장바구니에 추가되었습니다!",
        "cart": "쇼핑 카트",
        "empty_cart": "장바구니가 비어 있습니다.",
        "total": "총계",
        "proceed_checkout": "결제 진행",
        "redirect_stripe": "Stripe 결제로 리디렉션 중...",
        "complete_payment": "결제를 완료하려면 여��를 클릭하세요",
        "checkout_error": "결제 세션 생성 오류: {error}",
        "payment_success": "결제 성공!",
        "payment_canceled": "결제가 취소되었습니다.",
        "cart_items": "장바구니 ({count})",
        "details_header": "도서 상세 정보",
        "page_count": "페이지 수",
        "trim_size": "판형",
        "interior_color": "내지 색상",
        "binding": "제본 방식",
        "keywords": "키워드",
        "toc": "목차",
        "bisac_codes": "BISAC 코드",
        "publication_date": "발행일",
        "login_to_checkout": "결제를 진행하려면 로그인해주세요."
    }
}

def get_translation(lang: str, key: str, **kwargs) -> str:
    '''
    Retrieves a translated string for the given key and language.

    Args:
        lang (str): The desired language code (e.g., 'en', 'ko').
        key (str): The key for the string to translate.
        **kwargs: Optional arguments for f-string formatting.

    Returns:
        str: The translated string, or a fallback message if not found.
    '''
    try:
        return translations[lang][key].format(**kwargs)
    except KeyError:
        # Fallback to English if translation is missing for the current language
        if lang != "en" and key in translations.get("en", {}):
            logging.warning(f"Translation key '{key}' not found for '{lang}'. Falling back to English.")
            return translations["en"][key].format(**kwargs)
        
        logging.warning(f"Translation key '{key}' not found for language '{lang}' and no English fallback exists.")
        return f"[{key.upper()}]"
    except Exception as e:
        logging.error(f"Error formatting translation for key '{key}' with args {kwargs}: {e}")
        return f"[{key.upper()}_FORMAT_ERROR]"