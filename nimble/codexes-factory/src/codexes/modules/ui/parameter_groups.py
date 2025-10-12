"""
Parameter Organization System for Streamlit UI
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class ParameterType(Enum):
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    MULTISELECT = "multiselect"
    FILE = "file"
    CHECKBOX = "checkbox"
    TEXTAREA = "textarea"
    JSON = "json"
    COLOR = "color"
    DATE = "date"
    CURRENCY = "currency"


@dataclass
class ConfigurationParameter:
    name: str
    display_name: str
    parameter_type: ParameterType
    default_value: Any
    help_text: str
    validation_rules: List[str]
    dependencies: List[str]
    group: str
    required: bool = False
    options: List[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    placeholder: Optional[str] = None


@dataclass
class ParameterGroup:
    name: str
    display_name: str
    description: str
    parameters: List[ConfigurationParameter]
    expanded_by_default: bool = False
    dependencies: List[str] = None
    display_modes: List[str] = None  # simple, advanced, expert


class ParameterGroupManager:
    """Organize parameters into logical groups for UI presentation"""
    
    def __init__(self):
        self.parameter_definitions = self._define_parameters()
        self.group_definitions = self._define_groups()
    
    def _define_parameters(self) -> Dict[str, ConfigurationParameter]:
        """Define all available parameters"""
        params = {}
        
        # Core Settings Parameters
        params['publisher'] = ConfigurationParameter(
            name='publisher',
            display_name='Publisher',
            parameter_type=ParameterType.SELECT,
            default_value='',
            help_text='The publishing company name',
            validation_rules=['required'],
            dependencies=[],
            group='core_settings',
            required=True
        )
        
        params['imprint'] = ConfigurationParameter(
            name='imprint',
            display_name='Imprint',
            parameter_type=ParameterType.SELECT,
            default_value='',
            help_text='The publishing imprint or brand',
            validation_rules=['required'],
            dependencies=['publisher'],
            group='core_settings',
            required=True
        )
        
        params['tranche'] = ConfigurationParameter(
            name='tranche',
            display_name='Tranche',
            parameter_type=ParameterType.SELECT,
            default_value='',
            help_text='The batch or tranche configuration',
            validation_rules=[],
            dependencies=['imprint'],
            group='core_settings'
        )
        
        params['schedule_file'] = ConfigurationParameter(
            name='schedule_file',
            display_name='Schedule File',
            parameter_type=ParameterType.FILE,
            default_value=None,
            help_text='JSON file containing the book schedule',
            validation_rules=['required'],
            dependencies=[],
            group='core_settings',
            required=True
        )
        
        params['model'] = ConfigurationParameter(
            name='model',
            display_name='Primary LLM Model',
            parameter_type=ParameterType.SELECT,
            default_value='gemini/gemini-2.5-flash',
            help_text='The main model for content generation',
            validation_rules=['required'],
            dependencies=[],
            group='core_settings',
            required=True,
            options=[
                'gemini/gemini-2.5-flash',
                'gemini/gemini-2.5-pro',
                'openai/gpt-4o',
                'openai/gpt-4-turbo',
                'anthropic/claude-3-opus',
                'anthropic/claude-3-sonnet',
                'anthropic/claude-3-haiku'
            ]
        )
        
        params['verifier_model'] = ConfigurationParameter(
            name='verifier_model',
            display_name='Verifier LLM Model',
            parameter_type=ParameterType.SELECT,
            default_value='gemini/gemini-2.5-pro',
            help_text='A high-quality model for quote verification',
            validation_rules=[],
            dependencies=[],
            group='core_settings',
            options=[
                'gemini/gemini-2.5-flash',
                'gemini/gemini-2.5-pro',
                'openai/gpt-4o',
                'openai/gpt-4-turbo',
                'anthropic/claude-3-opus',
                'anthropic/claude-3-sonnet',
                'anthropic/claude-3-haiku'
            ]
        )
        
        # LSI Configuration Parameters
        params['lightning_source_account'] = ConfigurationParameter(
            name='lightning_source_account',
            display_name='Lightning Source Account #',
            parameter_type=ParameterType.TEXT,
            default_value='6024045',
            help_text='Your Lightning Source account number',
            validation_rules=['required', 'numeric'],
            dependencies=[],
            group='lsi_configuration',
            required=True
        )
        
        params['rendition_booktype'] = ConfigurationParameter(
            name='rendition_booktype',
            display_name='Rendition Book Type',
            parameter_type=ParameterType.SELECT,
            default_value='Perfect Bound',
            help_text='The book binding type for LSI',
            validation_rules=['required'],
            dependencies=[],
            group='lsi_configuration',
            required=True,
            options=[
                'Perfect Bound',
                'POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE',
                'POD: Standard B&W 6 x 9 in or 229 x 152 mm Case Lam w/Jacket on Standard 70 White w/Matte Lam'
            ]
        )
        
        params['cover_submission_method'] = ConfigurationParameter(
            name='cover_submission_method',
            display_name='Cover Submission Method',
            parameter_type=ParameterType.SELECT,
            default_value='FTP',
            help_text='How cover files are submitted to LSI',
            validation_rules=['required'],
            dependencies=[],
            group='lsi_configuration',
            required=True,
            options=['FTP', 'Upload', 'Email']
        )
        
        params['text_block_submission_method'] = ConfigurationParameter(
            name='text_block_submission_method',
            display_name='Text Block Submission Method',
            parameter_type=ParameterType.SELECT,
            default_value='FTP',
            help_text='How interior files are submitted to LSI',
            validation_rules=['required'],
            dependencies=[],
            group='lsi_configuration',
            required=True,
            options=['FTP', 'Upload', 'Email']
        )
        
        # Physical Specifications
        params['trim_size'] = ConfigurationParameter(
            name='trim_size',
            display_name='Trim Size',
            parameter_type=ParameterType.SELECT,
            default_value='6x9',
            help_text='The physical dimensions of the book',
            validation_rules=['required'],
            dependencies=[],
            group='physical_specifications',
            required=True,
            options=['5x8', '5.5x8.5', '6x9', '7x10', '8x10', '8.5x11', 'Custom']
        )
        
        params['page_count'] = ConfigurationParameter(
            name='page_count',
            display_name='Page Count',
            parameter_type=ParameterType.NUMBER,
            default_value=200,
            help_text='Total number of pages in the book',
            validation_rules=['required', 'positive'],
            dependencies=[],
            group='physical_specifications',
            required=True,
            min_value=1,
            max_value=2000
        )
        
        params['binding_type'] = ConfigurationParameter(
            name='binding_type',
            display_name='Binding Type',
            parameter_type=ParameterType.SELECT,
            default_value='paperback',
            help_text='The type of book binding',
            validation_rules=['required'],
            dependencies=[],
            group='physical_specifications',
            required=True,
            options=['paperback', 'hardcover', 'spiral', 'saddle-stitched']
        )
        
        params['interior_color'] = ConfigurationParameter(
            name='interior_color',
            display_name='Interior Color',
            parameter_type=ParameterType.SELECT,
            default_value='BW',
            help_text='Interior printing color specification',
            validation_rules=['required'],
            dependencies=[],
            group='physical_specifications',
            required=True,
            options=['BW', 'Color', 'Black and White']
        )
        
        params['interior_paper'] = ConfigurationParameter(
            name='interior_paper',
            display_name='Interior Paper',
            parameter_type=ParameterType.SELECT,
            default_value='white',
            help_text='Interior paper color/type',
            validation_rules=['required'],
            dependencies=[],
            group='physical_specifications',
            required=True,
            options=['white', 'cream', 'Cream', 'White']
        )
        
        params['cover_type'] = ConfigurationParameter(
            name='cover_type',
            display_name='Cover Type',
            parameter_type=ParameterType.SELECT,
            default_value='matte',
            help_text='Cover finish type',
            validation_rules=['required'],
            dependencies=[],
            group='physical_specifications',
            required=True,
            options=['matte', 'gloss', 'Paperback', 'Matte', 'Gloss']
        )
        
        # Territorial Pricing
        params['us_wholesale_discount'] = ConfigurationParameter(
            name='us_wholesale_discount',
            display_name='US Wholesale Discount %',
            parameter_type=ParameterType.NUMBER,
            default_value=40,
            help_text='Wholesale discount percentage for US market',
            validation_rules=['required', 'percentage'],
            dependencies=[],
            group='territorial_pricing',
            required=True,
            min_value=0,
            max_value=100
        )
        
        params['uk_wholesale_discount'] = ConfigurationParameter(
            name='uk_wholesale_discount',
            display_name='UK Wholesale Discount %',
            parameter_type=ParameterType.NUMBER,
            default_value=40,
            help_text='Wholesale discount percentage for UK market',
            validation_rules=['required', 'percentage'],
            dependencies=[],
            group='territorial_pricing',
            required=True,
            min_value=0,
            max_value=100
        )
        
        params['eu_wholesale_discount'] = ConfigurationParameter(
            name='eu_wholesale_discount',
            display_name='EU Wholesale Discount %',
            parameter_type=ParameterType.NUMBER,
            default_value=40,
            help_text='Wholesale discount percentage for EU market',
            validation_rules=['required', 'percentage'],
            dependencies=[],
            group='territorial_pricing',
            required=True,
            min_value=0,
            max_value=100
        )
        
        # Metadata Defaults
        params['language_code'] = ConfigurationParameter(
            name='language_code',
            display_name='Language Code',
            parameter_type=ParameterType.SELECT,
            default_value='eng',
            help_text='ISO language code for the book',
            validation_rules=['required'],
            dependencies=[],
            group='metadata_defaults',
            required=True,
            options=['eng', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'jpn', 'kor', 'zho']
        )
        
        params['audience'] = ConfigurationParameter(
            name='audience',
            display_name='Audience',
            parameter_type=ParameterType.SELECT,
            default_value='General Adult',
            help_text='Target audience for the book',
            validation_rules=['required'],
            dependencies=[],
            group='metadata_defaults',
            required=True,
            options=['General Adult', 'Young Adult', 'Children', 'Academic', 'Professional']
        )
        
        params['bisac_category'] = ConfigurationParameter(
            name='bisac_category',
            display_name='BISAC Category',
            parameter_type=ParameterType.TEXT,
            default_value='',
            help_text='Primary BISAC subject category',
            validation_rules=[],
            dependencies=[],
            group='metadata_defaults',
            placeholder='e.g., SELF-HELP / Personal Growth'
        )
        
        # Pipeline Control
        params['start_stage'] = ConfigurationParameter(
            name='start_stage',
            display_name='Start Stage',
            parameter_type=ParameterType.SELECT,
            default_value=1,
            help_text='Pipeline stage to start from',
            validation_rules=['required'],
            dependencies=[],
            group='pipeline_control',
            required=True,
            options=[1, 2, 3, 4]
        )
        
        params['end_stage'] = ConfigurationParameter(
            name='end_stage',
            display_name='End Stage',
            parameter_type=ParameterType.SELECT,
            default_value=4,
            help_text='Pipeline stage to end at',
            validation_rules=['required'],
            dependencies=[],
            group='pipeline_control',
            required=True,
            options=[1, 2, 3, 4]
        )
        
        params['max_books'] = ConfigurationParameter(
            name='max_books',
            display_name='Max Books',
            parameter_type=ParameterType.NUMBER,
            default_value=1,
            help_text='Maximum number of books to process',
            validation_rules=['positive'],
            dependencies=[],
            group='pipeline_control',
            min_value=1,
            max_value=100
        )
        
        # LLM Configuration
        params['max_retries'] = ConfigurationParameter(
            name='max_retries',
            display_name='Max Retries',
            parameter_type=ParameterType.NUMBER,
            default_value=5,
            help_text='Maximum number of retry attempts for LLM calls',
            validation_rules=['positive'],
            dependencies=[],
            group='llm_configuration',
            min_value=1,
            max_value=10
        )
        
        params['base_delay'] = ConfigurationParameter(
            name='base_delay',
            display_name='Base Delay (seconds)',
            parameter_type=ParameterType.NUMBER,
            default_value=1.0,
            help_text='Base delay for exponential backoff',
            validation_rules=['positive'],
            dependencies=[],
            group='llm_configuration',
            min_value=0.1,
            max_value=5.0,
            step=0.1
        )
        
        params['enable_llm_completion'] = ConfigurationParameter(
            name='enable_llm_completion',
            display_name='Enable LLM Field Completion',
            parameter_type=ParameterType.CHECKBOX,
            default_value=True,
            help_text='Use AI to complete missing LSI metadata fields',
            validation_rules=[],
            dependencies=[],
            group='llm_configuration'
        )
        
        # Additional LSI Configuration Parameters
        params['carton_pack_quantity'] = ConfigurationParameter(
            name='carton_pack_quantity',
            display_name='Carton Pack Quantity',
            parameter_type=ParameterType.TEXT,
            default_value='1',
            help_text='Number of books per carton for shipping',
            validation_rules=[],
            dependencies=[],
            group='lsi_configuration'
        )
        
        params['order_type_eligibility'] = ConfigurationParameter(
            name='order_type_eligibility',
            display_name='Order Type Eligibility',
            parameter_type=ParameterType.SELECT,
            default_value='POD',
            help_text='Type of orders this book is eligible for',
            validation_rules=[],
            dependencies=[],
            group='lsi_configuration',
            options=['POD', 'Offset', 'Both']
        )
        
        params['territorial_rights'] = ConfigurationParameter(
            name='territorial_rights',
            display_name='Territorial Rights',
            parameter_type=ParameterType.SELECT,
            default_value='World',
            help_text='Geographic rights for distribution',
            validation_rules=['required'],
            dependencies=[],
            group='lsi_configuration',
            required=True,
            options=['World', 'US', 'North America', 'English Language', 'Custom']
        )
        
        params['returnability'] = ConfigurationParameter(
            name='returnability',
            display_name='Returnability',
            parameter_type=ParameterType.SELECT,
            default_value='Yes-Destroy',
            help_text='Return policy for unsold books',
            validation_rules=[],
            dependencies=[],
            group='lsi_configuration',
            options=['Yes', 'Yes-Destroy', 'No']
        )
        
        # Additional Territorial Pricing
        params['ca_wholesale_discount'] = ConfigurationParameter(
            name='ca_wholesale_discount',
            display_name='Canada Wholesale Discount %',
            parameter_type=ParameterType.NUMBER,
            default_value=40,
            help_text='Wholesale discount percentage for Canadian market',
            validation_rules=['percentage'],
            dependencies=[],
            group='territorial_pricing',
            min_value=0,
            max_value=100
        )
        
        params['au_wholesale_discount'] = ConfigurationParameter(
            name='au_wholesale_discount',
            display_name='Australia Wholesale Discount %',
            parameter_type=ParameterType.NUMBER,
            default_value=40,
            help_text='Wholesale discount percentage for Australian market',
            validation_rules=['percentage'],
            dependencies=[],
            group='territorial_pricing',
            min_value=0,
            max_value=100
        )
        
        # Additional Metadata Parameters
        params['country_of_origin'] = ConfigurationParameter(
            name='country_of_origin',
            display_name='Country of Origin',
            parameter_type=ParameterType.SELECT,
            default_value='US',
            help_text='Country where the book is published',
            validation_rules=['required'],
            dependencies=[],
            group='metadata_defaults',
            required=True,
            options=['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'IT', 'ES', 'JP', 'KR']
        )
        
        params['edition_number'] = ConfigurationParameter(
            name='edition_number',
            display_name='Edition Number',
            parameter_type=ParameterType.NUMBER,
            default_value=1,
            help_text='Edition number of the book',
            validation_rules=['positive'],
            dependencies=[],
            group='metadata_defaults',
            min_value=1,
            max_value=99
        )
        
        params['edition_description'] = ConfigurationParameter(
            name='edition_description',
            display_name='Edition Description',
            parameter_type=ParameterType.TEXT,
            default_value='First Edition',
            help_text='Description of the edition',
            validation_rules=[],
            dependencies=[],
            group='metadata_defaults'
        )
        
        params['series_name'] = ConfigurationParameter(
            name='series_name',
            display_name='Series Name',
            parameter_type=ParameterType.TEXT,
            default_value='',
            help_text='Name of the book series (if applicable)',
            validation_rules=[],
            dependencies=[],
            group='metadata_defaults'
        )
        
        params['contributor_one_role'] = ConfigurationParameter(
            name='contributor_one_role',
            display_name='Primary Contributor Role',
            parameter_type=ParameterType.SELECT,
            default_value='A',
            help_text='Role of the primary contributor (ONIX code)',
            validation_rules=[],
            dependencies=[],
            group='metadata_defaults',
            options=['A', 'B01', 'B06', 'E07', 'A01', 'Author', 'Editor', 'Translator']
        )
        
        # Enhanced LLM Configuration
        params['max_delay'] = ConfigurationParameter(
            name='max_delay',
            display_name='Max Delay (seconds)',
            parameter_type=ParameterType.NUMBER,
            default_value=60.0,
            help_text='Maximum delay between retries',
            validation_rules=['positive'],
            dependencies=[],
            group='llm_configuration',
            min_value=5.0,
            max_value=300.0,
            step=5.0
        )
        
        params['model_params_file'] = ConfigurationParameter(
            name='model_params_file',
            display_name='Model Parameters File',
            parameter_type=ParameterType.TEXT,
            default_value='resources/json/model_params.json',
            help_text='Path to JSON file with model parameters',
            validation_rules=[],
            dependencies=[],
            group='llm_configuration'
        )
        
        params['enable_isbn_assignment'] = ConfigurationParameter(
            name='enable_isbn_assignment',
            display_name='Enable ISBN Assignment',
            parameter_type=ParameterType.CHECKBOX,
            default_value=True,
            help_text='Automatically assign ISBNs to books that need them',
            validation_rules=[],
            dependencies=[],
            group='llm_configuration'
        )
        
        # Additional Pipeline Control
        params['begin_with_book'] = ConfigurationParameter(
            name='begin_with_book',
            display_name='Begin with Book #',
            parameter_type=ParameterType.NUMBER,
            default_value=1,
            help_text='Book number to start with (1-based index)',
            validation_rules=['positive'],
            dependencies=[],
            group='pipeline_control',
            min_value=1,
            max_value=1000
        )
        
        params['end_with_book'] = ConfigurationParameter(
            name='end_with_book',
            display_name='End with Book #',
            parameter_type=ParameterType.NUMBER,
            default_value=0,
            help_text='Book number to end with (0 = process until the end)',
            validation_rules=[],
            dependencies=[],
            group='pipeline_control',
            min_value=0,
            max_value=1000
        )
        
        params['quotes_per_book'] = ConfigurationParameter(
            name='quotes_per_book',
            display_name='Quotes Per Book',
            parameter_type=ParameterType.NUMBER,
            default_value=0,
            help_text='Override the number of quotes per book (0 = use default)',
            validation_rules=[],
            dependencies=[],
            group='pipeline_control',
            min_value=0,
            max_value=1000,
            step=10
        )
        
        params['only_run_prompts'] = ConfigurationParameter(
            name='only_run_prompts',
            display_name='Only Run Specific Prompts',
            parameter_type=ParameterType.TEXT,
            default_value='',
            help_text='Comma-separated list of prompt keys to run (e.g., quotes,mnemonics)',
            validation_rules=[],
            dependencies=[],
            group='pipeline_control',
            placeholder='quotes,mnemonics,summary'
        )
        
        # Advanced Configuration
        params['catalog_file'] = ConfigurationParameter(
            name='catalog_file',
            display_name='Catalog File',
            parameter_type=ParameterType.TEXT,
            default_value='data/books.csv',
            help_text='Filename for the output catalog',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        params['base_dir'] = ConfigurationParameter(
            name='base_dir',
            display_name='Base Directory',
            parameter_type=ParameterType.TEXT,
            default_value='',
            help_text='The base directory for the pipeline (default: output/{imprint}_build)',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        params['debug_cover'] = ConfigurationParameter(
            name='debug_cover',
            display_name='Debug Cover',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Run cover generation in debug mode',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        params['leave_build_dirs'] = ConfigurationParameter(
            name='leave_build_dirs',
            display_name='Leave Build Directories',
            parameter_type=ParameterType.CHECKBOX,
            default_value=True,
            help_text='Do not delete temporary build directories',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        params['catalog_only'] = ConfigurationParameter(
            name='catalog_only',
            display_name='Catalog Only',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Only generate the catalog',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        params['skip_catalog'] = ConfigurationParameter(
            name='skip_catalog',
            display_name='Skip Catalog',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Skip the storefront catalog generation',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        params['lsi_config'] = ConfigurationParameter(
            name='lsi_config',
            display_name='LSI Config File',
            parameter_type=ParameterType.TEXT,
            default_value='',
            help_text='Path to custom LSI configuration file',
            validation_rules=[],
            dependencies=[],
            group='lsi_configuration'
        )
        
        params['lsi_template'] = ConfigurationParameter(
            name='lsi_template',
            display_name='LSI Template',
            parameter_type=ParameterType.TEXT,
            default_value='templates/LSI_ACS_header.csv',
            help_text='Path to LSI template CSV file',
            validation_rules=[],
            dependencies=[],
            group='lsi_configuration'
        )
        
        params['report_formats'] = ConfigurationParameter(
            name='report_formats',
            display_name='Report Formats',
            parameter_type=ParameterType.MULTISELECT,
            default_value=['html'],
            help_text='Formats for generated reports',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration',
            options=['html', 'csv', 'json', 'markdown']
        )
        
        params['legacy_reports'] = ConfigurationParameter(
            name='legacy_reports',
            display_name='Use Legacy Reports',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Use only the legacy field report generator',
            validation_rules=[],
            dependencies=[],
            group='advanced_configuration'
        )
        
        # Debug and Monitoring
        params['verbose'] = ConfigurationParameter(
            name='verbose',
            display_name='Verbose Logging',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Enable verbose logging including Pydantic warnings',
            validation_rules=[],
            dependencies=[],
            group='debug_monitoring'
        )
        
        params['terse_log'] = ConfigurationParameter(
            name='terse_log',
            display_name='Terse Log',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Enable terse logging (only show status emojis)',
            validation_rules=[],
            dependencies=[],
            group='debug_monitoring'
        )
        
        params['show_prompt_logs'] = ConfigurationParameter(
            name='show_prompt_logs',
            display_name='Show Prompt Logs',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Show prompt name, prompt, and params being submitted to LLM',
            validation_rules=[],
            dependencies=[],
            group='debug_monitoring'
        )
        
        params['no_litellm_log'] = ConfigurationParameter(
            name='no_litellm_log',
            display_name='Suppress LiteLLM Logs',
            parameter_type=ParameterType.CHECKBOX,
            default_value=True,
            help_text='Suppress LiteLLM INFO logs',
            validation_rules=[],
            dependencies=[],
            group='debug_monitoring'
        )
        
        params['overwrite'] = ConfigurationParameter(
            name='overwrite',
            display_name='Overwrite Existing Files',
            parameter_type=ParameterType.CHECKBOX,
            default_value=True,
            help_text='Force re-running stages even if output files already exist',
            validation_rules=[],
            dependencies=[],
            group='pipeline_control'
        )
        
        params['enable_metadata_discovery'] = ConfigurationParameter(
            name='enable_metadata_discovery',
            display_name='Enable Metadata Discovery',
            parameter_type=ParameterType.CHECKBOX,
            default_value=False,
            help_text='Allow LLM to discover publisher, imprint, and author from content (for public domain works)',
            validation_rules=[],
            dependencies=[],
            group='llm_configuration'
        )
        
        params['no_litellm_log'] = ConfigurationParameter(
            name='no_litellm_log',
            display_name='No LiteLLM Log',
            parameter_type=ParameterType.CHECKBOX,
            default_value=True,
            help_text='Suppress LiteLLM INFO logs',
            validation_rules=[],
            dependencies=[],
            group='debug_monitoring'
        )
        
        return params
    
    def _define_groups(self) -> Dict[str, ParameterGroup]:
        """Define parameter groups"""
        groups = {}
        
        groups['core_settings'] = ParameterGroup(
            name='core_settings',
            display_name='Core Settings',
            description='Basic publishing information and model selection',
            parameters=[],  # Will be populated by get_group_parameters
            expanded_by_default=True,
            display_modes=['simple', 'advanced', 'expert']
        )
        
        groups['pipeline_control'] = ParameterGroup(
            name='pipeline_control',
            display_name='Pipeline Stages',
            description='Control which stages of the pipeline to run',
            parameters=[],
            expanded_by_default=True,
            display_modes=['simple', 'advanced', 'expert']
        )
        
        groups['lsi_configuration'] = ParameterGroup(
            name='lsi_configuration',
            display_name='LSI Configuration',
            description='Lightning Source specific settings',
            parameters=[],
            expanded_by_default=False,
            display_modes=['advanced', 'expert']
        )
        
        groups['physical_specifications'] = ParameterGroup(
            name='physical_specifications',
            display_name='Physical Specifications',
            description='Book dimensions, binding, and paper specifications',
            parameters=[],
            expanded_by_default=False,
            display_modes=['advanced', 'expert']
        )
        
        groups['territorial_pricing'] = ParameterGroup(
            name='territorial_pricing',
            display_name='Territorial Pricing',
            description='Multi-currency pricing and wholesale discounts',
            parameters=[],
            expanded_by_default=False,
            display_modes=['advanced', 'expert']
        )
        
        groups['metadata_defaults'] = ParameterGroup(
            name='metadata_defaults',
            display_name='Metadata Defaults',
            description='Default values for book metadata',
            parameters=[],
            expanded_by_default=False,
            display_modes=['advanced', 'expert']
        )
        
        groups['llm_configuration'] = ParameterGroup(
            name='llm_configuration',
            display_name='LLM & AI Configuration',
            description='AI model parameters and field completion settings',
            parameters=[],
            expanded_by_default=False,
            display_modes=['expert']
        )
        
        groups['advanced_configuration'] = ParameterGroup(
            name='advanced_configuration',
            display_name='Advanced Configuration',
            description='Advanced pipeline settings and file management',
            parameters=[],
            expanded_by_default=False,
            display_modes=['expert']
        )
        
        groups['debug_monitoring'] = ParameterGroup(
            name='debug_monitoring',
            display_name='Debug & Monitoring',
            description='Debug settings, logging, and performance monitoring',
            parameters=[],
            expanded_by_default=False,
            display_modes=['expert']
        )
        
        return groups
    
    def get_parameter_groups(self) -> Dict[str, ParameterGroup]:
        """Get parameter groups with populated parameters"""
        groups = self.group_definitions.copy()
        
        # Populate parameters for each group
        for group_name, group in groups.items():
            group.parameters = [
                param for param in self.parameter_definitions.values()
                if param.group == group_name
            ]
        
        return groups
    
    def get_group_parameters(self, group_name: str) -> List[ConfigurationParameter]:
        """Get parameters for a specific group"""
        return [
            param for param in self.parameter_definitions.values()
            if param.group == group_name
        ]
    
    def get_parameter_by_name(self, name: str) -> Optional[ConfigurationParameter]:
        """Get a parameter by name"""
        return self.parameter_definitions.get(name)
    
    def validate_parameter_dependencies(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameter dependencies"""
        errors = []
        
        for param_name, param_value in params.items():
            param_def = self.parameter_definitions.get(param_name)
            if not param_def:
                continue
                
            # Check dependencies
            for dependency in param_def.dependencies:
                if dependency not in params or not params[dependency]:
                    errors.append(f"{param_def.display_name} requires {dependency} to be set")
        
        return errors
    
    def get_parameter_help_text(self, param_name: str) -> str:
        """Get help text for a parameter"""
        param = self.parameter_definitions.get(param_name)
        return param.help_text if param else ""
    
    def get_parameters_for_display_mode(self, display_mode: str) -> Dict[str, List[ConfigurationParameter]]:
        """Get parameters organized by group for a specific display mode"""
        result = {}
        groups = self.get_parameter_groups()
        
        for group_name, group in groups.items():
            if display_mode in (group.display_modes or ['simple']):
                result[group_name] = group.parameters
        
        return result