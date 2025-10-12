# tests/test_data/sample_metadata.py

"""
Sample metadata objects for testing LSI field enhancement system.
Provides metadata with various completeness levels for comprehensive testing.
"""

from src.codexes.modules.metadata.metadata_models import CodexMetadata
from datetime import datetime, timedelta


def create_minimal_metadata():
    """
    Create metadata with only the most basic required fields.
    Useful for testing field completion and default value application.
    """
    return CodexMetadata(
        title="The Future of Technology",
        author="Dr. Sarah Johnson",
        isbn13="9781234567890",
        publisher="Tech Publications"
    )


def create_complete_metadata():
    """
    Create metadata with all major fields populated.
    Useful for testing comprehensive field mapping and validation.
    """
    return CodexMetadata(
        # Basic book information
        title="Artificial Intelligence: A Comprehensive Guide",
        subtitle="Understanding Machine Learning and Deep Learning",
        author="Dr. Sarah Johnson",
        isbn13="9781234567890",
        isbn10="1234567890",
        publisher="Tech Publications",
        imprint="AI Research Series",
        
        # Content information
        summary_long="This comprehensive guide explores the fascinating world of artificial intelligence, covering everything from basic machine learning concepts to advanced deep learning techniques. Written for both beginners and experienced practitioners, this book provides practical insights and real-world applications of AI technologies.",
        summary_short="A comprehensive guide to artificial intelligence covering machine learning and deep learning for all skill levels.",
        keywords="artificial intelligence; machine learning; deep learning; neural networks; data science; technology",
        table_of_contents="1. Introduction to AI\n2. Machine Learning Fundamentals\n3. Deep Learning\n4. Neural Networks\n5. Practical Applications\n6. Future of AI",
        
        # Classification
        bisac_codes="COM004000; TEC009000; SCI010000",
        bisac_category_2="TEC009000",
        bisac_category_3="SCI010000",
        thema_codes="UYQ; UYQM; PDZ",
        audience="General Adult",
        min_age="18",
        max_age="99",
        language="eng",
        country_of_origin="US",
        
        # Physical specifications
        page_count=350,
        trim_size="6 x 9",
        trim_width_in="6",
        trim_height_in="9",
        binding="Perfect Bound",
        interior_color="Black & White",
        interior_paper="White",
        cover_type="Matte",
        weight_lbs="1.2",
        
        # Pricing and distribution
        list_price_usd=29.99,
        us_wholesale_discount="40",
        uk_wholesale_discount="40",
        eu_wholesale_discount="40",
        returns_allowed="Yes",
        returnability="Yes-Destroy",
        territorial_rights="World",
        
        # Publication information
        publication_date="2024-03-15",
        street_date="2024-03-15",
        edition_number="1",
        edition_description="First Edition",
        
        # Contributors
        contributor_one_bio="Dr. Sarah Johnson is a leading researcher in artificial intelligence with over 15 years of experience in machine learning and neural networks. She holds a Ph.D. in Computer Science from MIT and has published numerous papers on AI applications.",
        contributor_one_affiliations="MIT Computer Science Department",
        contributor_one_professional_position="Professor of Computer Science",
        contributor_one_location="Cambridge, MA",
        contributor_one_location_type_code="US-MA",
        contributor_one_prior_work="Machine Learning Fundamentals (2020), Neural Network Design (2018)",
        
        # Series information
        series_name="AI Research Series",
        series_number="1",
        volume_number="1",
        
        # LSI specific fields
        lightning_source_account="6024045",
        cover_submission_method="FTP",
        text_block_submission_method="FTP",
        carton_pack_quantity="1",
        order_type_eligibility="POD",
        
        # File paths
        jacket_path_filename="9781234567890_jacket.pdf",
        interior_path_filename="9781234567890_interior.pdf",
        cover_path_filename="9781234567890_cover.pdf",
        publisher_reference_id="TECH_AI_001",
        
        # Marketing
        review_quotes="'A masterful exploration of AI technologies' - Tech Review Magazine; 'Essential reading for anyone interested in artificial intelligence' - AI Today",
        marketing_image="ai_guide_marketing.jpg",
        
        # Illustrations
        illustration_count="25",
        illustration_notes="Diagrams, flowcharts, and technical illustrations throughout"
    )


def create_fiction_metadata():
    """
    Create metadata for a fiction book with genre-specific fields.
    """
    return CodexMetadata(
        # Basic information
        title="The Last Algorithm",
        subtitle="A Cyberpunk Thriller",
        author="Alex Chen",
        isbn13="9789876543210",
        publisher="Nimble Books LLC",
        imprint="Xynapse Traces",
        
        # Content
        summary_long="In a world where artificial intelligence controls every aspect of society, one programmer discovers a hidden algorithm that could change everything. Racing against time and powerful corporations, she must decide whether to expose the truth or protect the fragile balance of their digital world.",
        summary_short="A cyberpunk thriller about a programmer who discovers a dangerous AI algorithm that could change the world.",
        keywords="cyberpunk; thriller; artificial intelligence; dystopian; technology; science fiction",
        
        # Classification
        bisac_codes="FIC028000; FIC028010; FIC028070",
        audience="General Adult",
        min_age="16",
        max_age="99",
        language="eng",
        
        # Physical specs
        page_count=280,
        trim_size="5.25 x 8",
        trim_width_in="5.25",
        trim_height_in="8",
        binding="Perfect Bound",
        
        # Pricing
        list_price_usd=16.99,
        us_wholesale_discount="40",
        
        # Publication
        publication_date="2024-06-01",
        
        # Series
        series_name="Digital Futures",
        series_number="1",
        
        # Contributors
        contributor_one_bio="Alex Chen is a software engineer turned novelist who brings authentic technical expertise to speculative fiction.",
        
        # LSI fields
        publisher_reference_id="XYN_ALGO_001"
    )


def create_academic_metadata():
    """
    Create metadata for an academic/scholarly book.
    """
    return CodexMetadata(
        # Basic information
        title="Quantum Computing: Theory and Applications",
        subtitle="A Mathematical Approach",
        author="Prof. Maria Rodriguez",
        isbn13="9781111222333",
        publisher="Academic Press International",
        imprint="Science & Technology Series",
        
        # Content
        summary_long="This rigorous treatment of quantum computing provides a comprehensive mathematical foundation for understanding quantum algorithms, quantum error correction, and practical applications in cryptography and optimization. Designed for graduate students and researchers in computer science, physics, and mathematics.",
        summary_short="A comprehensive mathematical treatment of quantum computing theory and applications for graduate students and researchers.",
        keywords="quantum computing; quantum algorithms; quantum mechanics; cryptography; mathematics; computer science",
        table_of_contents="Part I: Mathematical Foundations\n1. Linear Algebra Review\n2. Quantum Mechanics Basics\nPart II: Quantum Algorithms\n3. Quantum Fourier Transform\n4. Shor's Algorithm\nPart III: Applications\n5. Quantum Cryptography\n6. Optimization Problems",
        
        # Classification
        bisac_codes="SCI057000; MAT003000; COM014000",
        audience="Professional/Scholarly",
        min_age="22",
        max_age="99",
        language="eng",
        
        # Physical specs
        page_count=450,
        trim_size="7 x 10",
        trim_width_in="7",
        trim_height_in="10",
        binding="Perfect Bound",
        
        # Academic pricing
        list_price_usd=89.99,
        us_wholesale_discount="20",
        uk_wholesale_discount="25",
        returnability="Yes-Return",
        
        # Publication
        publication_date="2024-09-01",
        edition_number="2",
        edition_description="Second Edition, Revised",
        
        # Contributors
        contributor_one_bio="Prof. Maria Rodriguez is a Professor of Physics at Stanford University, specializing in quantum information theory. She has published over 100 papers on quantum computing and is a recipient of the National Science Foundation CAREER Award.",
        contributor_one_affiliations="Stanford University Physics Department",
        contributor_one_professional_position="Professor of Physics",
        contributor_one_location="Stanford, CA",
        contributor_one_prior_work="Quantum Information Theory (2019), Introduction to Quantum Mechanics (2017)",
        
        # Academic specific
        territorial_rights="World English",
        lsi_special_category="Academic",
        publisher_reference_id="API_QC_002"
    )


def create_children_metadata():
    """
    Create metadata for a children's book.
    """
    return CodexMetadata(
        # Basic information
        title="The Robot Who Loved to Read",
        author="Emma Thompson",
        isbn13="9785555666777",
        publisher="Young Minds Publishing",
        imprint="STEM Kids",
        
        # Content
        summary_long="Join Robo as he discovers the joy of reading! This delightful story follows a curious robot who learns that books can take you on amazing adventures. Perfect for young readers who are just beginning their own reading journey.",
        summary_short="A charming story about a robot who discovers the joy of reading, perfect for beginning readers.",
        keywords="children's books; robots; reading; STEM; picture book; early readers",
        
        # Classification
        bisac_codes="JUV001000; JUV019000; JUV036000",
        audience="Juvenile",
        min_age="4",
        max_age="8",
        language="eng",
        
        # Physical specs
        page_count=32,
        trim_size="8.5 x 8.5",
        trim_width_in="8.5",
        trim_height_in="8.5",
        binding="Perfect Bound",
        interior_color="Full Color",
        
        # Pricing
        list_price_usd=12.99,
        us_wholesale_discount="45",
        
        # Publication
        publication_date="2024-04-15",
        
        # Contributors
        contributor_one_bio="Emma Thompson is a children's author and former elementary school teacher who loves inspiring young minds through storytelling.",
        
        # Illustrations
        illustration_count="16",
        illustration_notes="Full-color illustrations on every page",
        
        # Children's book specific
        publisher_reference_id="YMP_ROBOT_001"
    )


def create_incomplete_metadata():
    """
    Create metadata with many missing fields to test field completion.
    """
    return CodexMetadata(
        title="Mysteries of the Deep Ocean",
        author="Dr. James Wilson",
        isbn13="9782222333444",
        publisher="Ocean Science Press",
        page_count=200,
        list_price_usd=24.99,
        # Many fields intentionally left empty for completion testing
        summary_long="",
        summary_short="",
        keywords="",
        bisac_codes="",
        contributor_one_bio="",
        audience="",
        min_age="",
        max_age=""
    )


def create_international_metadata():
    """
    Create metadata for a book with international distribution focus.
    """
    return CodexMetadata(
        # Basic information
        title="Global Economics in the Digital Age",
        subtitle="Perspectives from Around the World",
        author="Dr. Yuki Tanaka",
        isbn13="9783333444555",
        publisher="International Academic Publishers",
        
        # Content
        summary_long="This comprehensive analysis examines how digital technologies are reshaping global economic systems, with case studies from Asia, Europe, and the Americas. Essential reading for economists, policymakers, and business leaders.",
        summary_short="An analysis of how digital technologies are reshaping global economic systems with international case studies.",
        keywords="global economics; digital transformation; international trade; economic policy; technology",
        
        # Classification
        bisac_codes="BUS069000; POL024000; TEC052000",
        audience="Professional/Scholarly",
        language="eng",
        
        # Physical specs
        page_count=320,
        trim_size="6 x 9",
        list_price_usd=45.99,
        
        # International distribution
        territorial_rights="World",
        us_wholesale_discount="35",
        uk_wholesale_discount="35",
        eu_wholesale_discount="35",
        
        # Publication
        publication_date="2024-07-01",
        
        # Contributors
        contributor_one_bio="Dr. Yuki Tanaka is an international economist and professor at Tokyo University, specializing in digital economics and global trade policy.",
        contributor_one_affiliations="Tokyo University Economics Department",
        contributor_one_location="Tokyo, Japan",
        
        # International specific
        country_of_origin="JP",
        publisher_reference_id="IAP_GLOBAL_001"
    )


def create_test_metadata_collection():
    """
    Create a collection of test metadata objects for comprehensive testing.
    
    Returns:
        dict: Dictionary of metadata objects with descriptive keys
    """
    return {
        'minimal': create_minimal_metadata(),
        'complete': create_complete_metadata(),
        'fiction': create_fiction_metadata(),
        'academic': create_academic_metadata(),
        'children': create_children_metadata(),
        'incomplete': create_incomplete_metadata(),
        'international': create_international_metadata()
    }


def get_metadata_by_completeness_level(level):
    """
    Get metadata object by completeness level.
    
    Args:
        level (str): Completeness level ('minimal', 'partial', 'complete')
        
    Returns:
        CodexMetadata: Metadata object at specified completeness level
    """
    if level == 'minimal':
        return create_minimal_metadata()
    elif level == 'partial':
        return create_incomplete_metadata()
    elif level == 'complete':
        return create_complete_metadata()
    else:
        raise ValueError(f"Unknown completeness level: {level}")


def get_metadata_by_genre(genre):
    """
    Get metadata object by genre/type.
    
    Args:
        genre (str): Genre type ('fiction', 'academic', 'children', 'technical')
        
    Returns:
        CodexMetadata: Metadata object for specified genre
    """
    if genre == 'fiction':
        return create_fiction_metadata()
    elif genre == 'academic':
        return create_academic_metadata()
    elif genre == 'children':
        return create_children_metadata()
    elif genre == 'technical':
        return create_complete_metadata()  # Technical AI book
    else:
        raise ValueError(f"Unknown genre: {genre}")


# Test data validation
def validate_test_metadata():
    """
    Validate all test metadata objects for consistency.
    """
    collection = create_test_metadata_collection()
    
    print("=== Test Metadata Validation ===")
    
    for name, metadata in collection.items():
        print(f"\n{name.upper()} METADATA:")
        
        # Check required fields
        required_fields = ['title', 'author', 'isbn13', 'publisher']
        missing_required = []
        
        for field in required_fields:
            if not getattr(metadata, field, None):
                missing_required.append(field)
        
        if missing_required:
            print(f"  ❌ Missing required fields: {missing_required}")
        else:
            print(f"  ✅ All required fields present")
        
        # Check ISBN format
        isbn = metadata.isbn13
        if isbn and len(isbn.replace('-', '').replace(' ', '')) == 13:
            print(f"  ✅ ISBN format valid: {isbn}")
        else:
            print(f"  ❌ ISBN format invalid: {isbn}")
        
        # Count populated fields
        all_fields = [attr for attr in dir(metadata) if not attr.startswith('_') and not callable(getattr(metadata, attr))]
        populated = sum(1 for field in all_fields if getattr(metadata, field, None))
        
        print(f"  📊 Populated fields: {populated}/{len(all_fields)} ({populated/len(all_fields)*100:.1f}%)")


if __name__ == "__main__":
    # Run validation when script is executed directly
    validate_test_metadata()