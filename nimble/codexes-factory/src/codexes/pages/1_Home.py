import logging
import streamlit as st
import sys
sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()




logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)




from codexes.core.utils import read_markdown_file


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")


# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app
# DO NOT render sidebar here - it's already rendered by codexes-factory-home-ui.py

# Sync session state from shared auth
if is_authenticated():
    user_info = get_user_info()
    st.session_state.username = user_info.get('username')
    st.session_state.user_name = user_info.get('user_name')
    st.session_state.user_email = user_info.get('user_email')
    logger.info(f"User authenticated via shared auth: {st.session_state.username}")
else:
    if "username" not in st.session_state:
        st.session_state.username = None




# Note: Unified sidebar is rendered by the main entry point (codexes-factory-home-ui.py)
# No need to call here

st.title("👨‍🔬AI Lab for Book-Lovers")
st.header("Humans Using Models to Make Books Richer, More Diverse, and More Surprising")
st.caption("A service of Nimble Books LLC, powered by codexes-factory")

with st.expander("Mission Statement", expanded=True):
    st.markdown(f"""

#### My goals:

- Minimally, make sure the advent of Artificial General Intelligence (AGI) doesn't kill the world of books.
- Maximally, use AGI to shape a world where books are more important, vital, and ubiquitous than ever before.

#### Along the way:
- Pass the critical quality threshold so that some AI- and AI-human collaborative books, matched head-to-head with comparable human books, _are as good as anything ever written by a human_.
- Operate the AI Lab for Book-Lovers where authors can experiment with tools for high-quality book writing.
- Pay for my retirement.

#### How you can help make AGI beneficial for book-lovers:

- let's get acquainted! 
    - [e-mail](mailto:wfz@nimblebooks.com); Signal (TK); [Substack](https://fredzannarbor.substack.com/).
    - Socials: [X](https://x.com/fredzannarbor), [Threads](https://www.threads.com/@fredzimmerman), [Facebook](https://www.facebook.com/fred.zimmerman1), [LinkedIn](https://www.linkedin.com/in/wfzimmerman).
- Read my Longform thinkpiece from 2021, which has held up pretty well.  
- Browse the Nimble Books catalog, which combines both traditional and AI-assisted publications.
- Check out my AI-powered imprints, **Text Hip Global** and **xynapse traces**.
- Try out some of my Lab tools, or share some of your own.  [Join the Substack](https://fredzannarbor.substack.com/) and drop me a note.
    """
)
with st.expander("The Longform Prospectus (January 2021)", expanded=False):
    longform_article = read_markdown_file("docs/resources/longform_prospectus.md")
    st.markdown(longform_article)

    st.markdown("""
    ### References

    Beltagy, Iz, Matthew E. Peters, and Arman Cohan. "Longformer: The long-document transformer." arXiv preprint arXiv:2004.05150 (2020).

    Boorstin, Daniel Joseph. The discoverers:[a history of man's search to know world and himself]. Vintage, 1985.

    Dickens, Charles. A Tale of Two Cities. Chapman & Hall, 1859.

    Egri, Lajos. The art of dramatic writing: Its basis in the creative interpretation of human motives. Simon and Schuster, 1972.

    McDermott, Joseph P. A social history of the Chinese book: books and literati culture in late imperial China. Vol. 1. Hong Kong University Press, 2006.

    McKee, Robert. Story: Substance, Structure, Style, and the Principles of Screenwriting. United Kingdom: Methuen, 1999.

    McLuhan, Marshall. "The Gutenberg Galaxy [1962]." New York: Signet (1969).O'Reilly Media. ORM Book Proposal. 2021. https://docs.google.com/document/d/16B8ZmpEj-DULGNb8X2NjpQPUnZMWUn5kM1ZBaN7pSUs/copy

    PageKicker. Algorithmic book creation. http://www.github.com/fredzannarbor/pagekicker-community

    Rasmy, Laila, Yang Xiang, Ziqian Xie, Cui Tao, and Degui Zhi. "Med-BERT: pre-trained contextualized embeddings on large-scale structured electronic health records for disease prediction." arXiv preprint arXiv:2005.12833 (2020).

    Rein, Judy. How to Write a Book Proposal: The Insider's Step-by-Step Guide to Proposals that Get You Published. Fifth Edition. 2017. Writer's Digesst Books.

    Rosenfeld, Louis. Three simple techniques for developing your book’s structure. 2021. Three simple techniques for developing your book’s structure. https://medium.com/rosenfeld-media/three-simple-techniques-for-developing-your-books-structure-b28d24c7d850

    Rowling, J.K. Harry Potter and the Deathly Hallows. 2007. Bloomsbury.

    Rowling, J.K. J.K. Rowling Writes about Her Reasons for Speaking out on Sex and Gender Issues. 2020. https://www.dw.com/en/jk-rowling-says-she-survived-sexual-abuse-and-domestic-violence/a-53770327

    Snowdon, David A., Susan J. Kemper, James A. Mortimer, Lydia H. Greiner, David R. Wekstein, and William R. Markesbery. "Linguistic ability in early life and cognitive function and Alzheimer's disease in late life: Findings from the Nun Study." Jama 275, no. 7 (1996): 528-532.

    Tolkien, J.R.R. Return of the King. 1955. Houghton & Mifflin.

    Twain, Mark. Huckleberry Finn. 1884. Chatto & Windus.

    UNESCO. Reading in the Mobile Era. 2020. https://en.unesco.org/news/reading-mobile-era-0

    University of Chicago. Manual of Style (17th Edition). 2020.

    Xiong, Yunyang, Zhanpeng Zeng, Rudrasis Chakraborty, Mingxing Tan, Glenn Fung, Yin Li, and Vikas Singh. "Nystr" omformer: A Nystr" om-Based Algorithm for Approximating Self-Attention." arXiv preprint arXiv:2102.03902 (2021).

    Zaheer, Manzil, Guru Guruganesh, Avinava Dubey, Joshua Ainslie, Chris Alberti, Santiago Ontanon, Philip Pham et al. "Big bird: Transformers for longer sequences." arXiv preprint arXiv:2007.14062 (2020).
        """)

st.components.v1.iframe('https://fredzannarbor.substack.com/embed', height=320, scrolling=False)