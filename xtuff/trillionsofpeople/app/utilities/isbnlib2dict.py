
import isbnlib
import streamlit as st

st.title("AI-Enhanced Details about $BOOK_TITLE with ISBN $ISBN$")

@st.cache_data
def get_isbn_info_from_isbnlib(detail_isbn):
    isbn_info_dict = {}
    isbnlibstatus = True
    try:
        isbn_info = isbnlib.meta(detail_isbn)
        if isbn_info:
            isbn_info_dict.update(isbn_info)

        else:
            isbn_info = None
    except Exception as e:
        isbn_info = None


    try:
        isbn_description = isbnlib.desc(detail_isbn)
        if isbn_description:
            addme = {'description': isbn_description}
            isbn_info_dict = {**isbn_info_dict, **addme}

        else:
            isbn_description = None
    except Exception as e:
        isbn_description = None

        
    try:
        isbn_cover_images = isbnlib.cover(detail_isbn)
        isbn_info_dict = {**isbn_info_dict, **isbn_cover_images}
        isbn_thumbnail = isbn_cover_images[0]
        if isbn_thumbnail:
            with st.expander("Thumbnail Cover Image", expanded=True):
                st.image(isbn_thumbnail, width=240)
        else:
            isbn_thumbnail = None

    except Exception as e:
        isbn_thumbnail = None
        #st.info("No thumbnail cover image for this isbn.")

    # try:
    #     isbn_10 = isbnlib.to_isbn10(detail_isbn)
    #     buylink = 'https://www.amazon.com/dp/' + isbn_10 + '/&tag=internetbooa-20'
    #     url_string_variable = buylink
    #     text_string_variable = 'Buy this book on Amazon'
    #     link = f'[{text_string_variable}]({url_string_variable})'

    #     isbn_info_dict = {**isbn_info_dict, **{'buylink': buylink}}
    # except Exception as e:
    #     st.error("Could not convert this ISBN-13 to ISBN-10. There is probably an error in the ISBN-13.")

    return isbn_info_dict


detail_isbn = st.text_input("Enter ISBN-13 of book to get details about it.")
st.write(get_isbn_info_from_isbnlib(detail_isbn))


