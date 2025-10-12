# Repository Directory Structure

**Generated:** 2025-08-26 23:19:49
**Session:** cleanup_20250826_231949

## Overview

This document describes the current directory structure of the repository
after cleanup operations have been performed.

## Directory Structure

```
├── .env
├── .gitignore
├── __init__.py
├── __pycache__
│   ├── __init__.cpython-312.pyc
│   ├── generate_lsi_field_report.cpython-312.pyc
│   └── run_book_pipeline.cpython-312.pyc
├── analyze_repository.py
├── batch_output
│   ├── test_cli_sample2_to_synopsis.json
│   ├── test_cli_sample3_to_synopsis.json
│   ├── test_cli_sample_to_synopsis.json
│   └── test_cli_sample_transformed_to_synopsis.json
├── batch_transform_cli.py
├── cache
│   └── exchange_rates.json
├── catalog.csv
├── check_syntax.py
├── cleanup_reports
│   ├── cleanup_20250826_231916_initial_snapshot.json
│   ├── cleanup_20250826_231949_initial_snapshot.json
│   ├── cleanup_report_20250826_231917.json
│   ├── cleanup_report_20250826_231917.md
│   ├── cleanup_report_20250826_231949.html
│   ├── cleanup_report_20250826_231949.json
│   ├── cleanup_report_20250826_231949.md
│   ├── directory_structure_20250826_231917.md
│   ├── directory_structure_20250826_231949.md
│   ├── validation_summary_20250826_231917.md
│   └── validation_summary_20250826_231949.md
├── cleanup_temporary_files.py
├── clear_cache_and_rebuild.sh
├── compare_prompts.py
├── comprehensive_validation_results_20250826_231917.json
├── config
│   ├── streamlit_apps.json
│   └── user_config.json
├── config_unification_report.md
├── configs
│   ├── default_lsi_config.json
│   ├── examples
│   │   └── academic_publisher.json
│   ├── imprints
│   │   ├── creative_minds_publishing.json
│   │   ├── imprint_template.json
│   │   ├── tech_books_press.json
│   │   └── xynapse_traces.json
│   ├── isbn_schedule.json
│   ├── llm_monitoring_config.json
│   ├── llm_prompt_config.json
│   ├── logging_config.json
│   ├── publishers
│   │   ├── academic_publishers_inc.json
│   │   ├── nimble_books.json
│   │   └── publisher_template.json
│   └── tranches
│       ├── sample_tranche.json
│       └── xynapse_tranche_1.json
├── convenience_cleanup_report.md
├── converted_back.csv
├── create_mnemonics.py
├── cumulative.csv
├── custom_llm_get_book_data.py
├── daily_engine.db
├── data
│   ├── 20250821_1904_books.csv
│   ├── 20250822_1842_books.csv
│   ├── 20250822_1910_books.csv
│   ├── 20250823_0457_books.csv
│   ├── 20250823_0806_books.csv
│   ├── 20250823_0829_books.csv
│   ├── 20250823_0922_books.csv
│   ├── 20250823_0954_books.csv
│   ├── 20250823_1411_books.csv
│   ├── 20250823_1958_books.csv
│   ├── 20250824_0257_books.csv
│   ├── 20250824_0320_books.csv
│   ├── 20250824_1027_books.csv
│   ├── 20250824_1043_books.csv
│   ├── 20250824_1756_books.csv
│   ├── 20250824_1936_books.csv
│   ├── 20250824_1940_books.csv
│   ├── 20250824_1943_books.csv
│   ├── 20250824_1947_books.csv
│   ├── 20250824_1950_books.csv
│   ├── 20250824_2002_books.csv
│   ├── 20250824_2025_books.csv
│   ├── 20250824_2046_books.csv
│   ├── 20250824_2119_books.csv
│   ├── 20250824_2140_books.csv
│   ├── 20250825_0315_books.csv
│   ├── 20250825_0922_books.csv
│   ├── 20250825_1058_books.csv
│   ├── 20250825_1425_books.csv
│   ├── 20250825_1553_books.csv
│   ├── 20250825_1818_books.csv
│   ├── 20250825_1943_books.csv
│   ├── 20250825_1955_books.csv
│   ├── 20250825_2007_books.csv
│   ├── 20250825_2016_books.csv
│   ├── 20250825_2041_books.csv
│   ├── 20250825_2109_books.csv
│   ├── 20250825_2134_books.csv
│   ├── 20250825_2155_books.csv
│   ├── 20250825_2222_books.csv
│   ├── 20250826_0016_books.csv
│   ├── 20250826_0042_books.csv
│   ├── 20250826_0113_books.csv
│   ├── 20250826_0146_books.csv
│   ├── 20250826_0352_books.csv
│   ├── 20250826_0543_books.csv
│   ├── 20250826_1921_books.csv
│   ├── 20250826_2015_books.csv
│   ├── 20250826_2036_books.csv
│   ├── 20250826_2101_books.csv
│   ├── 20250826_2150_books.csv
│   ├── 20250826_2315_books.csv
│   ├── AR7
│   │   ├── AR7_outline.txt
│   │   └── Doc_12-WGII_AR7_Chapter_Outline.pdf
│   ├── July_2025
│   │   ├── AI-Driven_Science_Speed_versus_Safety_assembled_raw_responses.json
│   │   ├── Birth_Rate_Boost_Policy_versus_Freedom_assembled_raw_responses.json
│   │   ├── Free_Speech_Platforms_Openness_versus_Regulation_assembled_raw_responses.json
│   │   ├── Global_Renewables_Scale_versus_Scarcity_assembled_raw_responses.json
│   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_assembled_raw_responses.json
│   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency_assembled_raw_responses.json
│   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility_assembled_raw_responses.json
│   │   └── Visionary_Drive_Passion_versus_Peril_assembled_raw_responses.json
│   ├── bibliography_shopping_lists
│   │   ├── AI Governance Freedom versus Constraint_bibliography_shopping_list.html
│   │   ├── AIDriven Science Speed versus Safety_bibliography_shopping_list.html
│   │   ├── Cognitive Upgrades Necessity versus Luxury_bibliography_shopping_list.html
│   │   ├── Family Support Data versus Intuition_bibliography_shopping_list.html
│   │   ├── Global Renewables Scale versus Scarcity_bibliography_shopping_list.html
│   │   ├── Global Renewables_bibliography_shopping_list.html
│   │   ├── Glossary Fix Verification_bibliography_shopping_list.html
│   │   ├── Internet for All Inclusion versus Barriers_bibliography_shopping_list.html
│   │   ├── Knowledge Access Freedom versus Restriction_bibliography_shopping_list.html
│   │   ├── Knowledge Access_bibliography_shopping_list.html
│   │   ├── Mars Governance Autonomy versus Oversight_bibliography_shopping_list.html
│   │   ├── Mars Governance_bibliography_shopping_list.html
│   │   ├── Martian Commerce Local versus Interplanetary_bibliography_shopping_list.html
│   │   ├── Martian SelfReliance Isolation versus Earth Support_bibliography_shopping_list.html
│   │   ├── Martian SelfReliance_bibliography_shopping_list.html
│   │   ├── MindMachine Fusion Liberation versus Dependency_bibliography_shopping_list.html
│   │   ├── Policy Automation Efficiency versus Equity_bibliography_shopping_list.html
│   │   ├── Solar Expansion_bibliography_shopping_list.html
│   │   ├── Streamlined Governance Agility versus Oversight_bibliography_shopping_list.html
│   │   ├── Streamlined Governance_bibliography_shopping_list.html
│   │   ├── Subterranean Cities Efficiency versus Feasibility_bibliography_shopping_list.html
│   │   ├── Test Book_bibliography_shopping_list.html
│   │   ├── The Beauty of Astrophysics_bibliography_shopping_list.html
│   │   ├── The Future of Geoinformatics_bibliography_shopping_list.html
│   │   ├── The Future of Space Robotics_bibliography_shopping_list.html
│   │   ├── Underground Planning Resilience versus Accessibility_bibliography_shopping_list.html
│   │   ├── Why Hippopotamuses Are Terrifying_bibliography_shopping_list.html
│   │   └── bibliography_shopping_list.html
│   ├── books.csv
│   ├── cumulative.csv
│   ├── ideation.db
│   ├── ideation_test.db
│   ├── isbn_database.json
│   ├── master_catalog.csv
│   ├── pilsa_glossary.json
│   ├── sensitivity_standards.py
│   ├── test_idea.txt
│   ├── test_json
│   │   ├── AI-Driven_Science_Speed_versus_Safety.json
│   │   ├── Birth_Rate_Boost_Policy_versus_Freedom.json
│   │   ├── Free_Speech_Platforms_Openness_versus_Regulation.json
│   │   ├── Global_Renewables_Scale_versus_Scarcity.json
│   │   ├── Martian_Commerce_Local_versus_Interplanetary.json
│   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support.json
│   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency.json
│   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility.json
│   │   ├── Visionary_Drive_Passion_versus_Peril.json
│   │   └── test_book.json
│   ├── test_outline.txt
│   ├── test_series_registry.json
│   ├── test_simple.rtf
│   └── test_synopsis.txt
├── diagnose_llm_responses.py
├── direct_mnemonics.py
├── docs
│   ├── ACCURATE_REPORTING_SYSTEM_SUMMARY.md
│   ├── ADVANCED_IDEATION_INTEGRATION_SUMMARY.md
│   ├── ADVANCED_IDEATION_USAGE_GUIDE.md
│   ├── AUTH_AND_IMPRINT_FIXES_SUMMARY.md
│   ├── BACKWARD_COMPATIBILITY_VERIFICATION_SUMMARY.md
│   ├── BATCH_TRANSFORMATION_IMPLEMENTATION_SUMMARY.md
│   ├── BOOK_PRODUCTION_FIXES_COMPLETE_SUMMARY.md
│   ├── BOOK_PRODUCTION_FIXES_GUIDE.md
│   ├── CLI_BATCH_TRANSFORMATION_GUIDE.md
│   ├── CLI_IMPLEMENTATION_SUMMARY.md
│   ├── COMMAND_BUILDER_FIX_SUMMARY.md
│   ├── COMPLETE_UI_FIXES_SUMMARY.md
│   ├── CONFIG_SYNC_FIX_SUMMARY.md
│   ├── DATE_COMPUTATION_README.md
│   ├── DROPDOWN_REFRESH_FIX_SUMMARY.md
│   ├── ENHANCED_ERROR_HANDLER_SUMMARY.md
│   ├── ENHANCED_ERROR_HANDLING_README.md
│   ├── ENHANCED_PROMPTS_README.md
│   ├── ERROR_HANDLING_TEST_SUMMARY.md
│   ├── FEATURES_RESTORED_SUMMARY.md
│   ├── FILE_PATH_GENERATION_README.md
│   ├── FINAL_FIX_SUMMARY.md
│   ├── FINAL_INTEGRATION_STATUS.md
│   ├── FINAL_UI_FIXES_SUMMARY.md
│   ├── FINAL_VALIDATION_FIX_SUMMARY.md
│   ├── IDEATION_INTEGRATION_GUIDE.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── INTEGRATION_STATUS_SUMMARY.md
│   ├── INTELLIGENT_FALLBACKS_README.md
│   ├── ISBN_DATABASE_GUIDE.md
│   ├── ISBN_REBUILD_FUNCTIONALITY.md
│   ├── ISBN_SCHEDULE_ASSIGNMENT_SUMMARY.md
│   ├── ISBN_SYSTEM_CONSOLIDATION.md
│   ├── LEGACY_REFERENCES_FIXED.md
│   ├── LIVE_PIPELINE_TEST_RESULTS.md
│   ├── LIVE_PIPELINE_TEST_RESULTS_FIXED.md
│   ├── LOGGING_CONFIGURATION_GUIDE.md
│   ├── LOGGING_IMPROVEMENTS_IMPLEMENTATION_SUMMARY.md
│   ├── LOGGING_PERFORMANCE_VALIDATION_REPORT.md
│   ├── LSI_ACCEPTANCE_TEST_GUIDE.md
│   ├── LSI_ACCEPTANCE_TEST_PLAN.md
│   ├── LSI_API_REFERENCE.md
│   ├── LSI_BEST_PRACTICES.md
│   ├── LSI_CSV_GENERATION_GUIDE.md
│   ├── LSI_FIELD_ENHANCEMENT_GUIDE.md
│   ├── LSI_FIELD_ENHANCEMENT_PHASE4_README.md
│   ├── LSI_FIELD_ENHANCEMENT_README.md
│   ├── LSI_TROUBLESHOOTING_GUIDE.md
│   ├── MANUAL_ISBN_ASSIGNMENT_GUIDE.md
│   ├── METHOD_SIGNATURE_FIXES_SUMMARY.md
│   ├── MIGRATION_COMPLETE_SUMMARY.md
│   ├── MIGRATION_GUIDE.md
│   ├── MNEMONICS_TEX_GENERATION.md
│   ├── MNEMONIC_FORMATTING_EVALUATION.md
│   ├── MNEMONIC_PRACTICE_LAYOUT_GUIDE.md
│   ├── MNEMONIC_TROUBLESHOOTING_GUIDE.md
│   ├── MULTI_LEVEL_CONFIG_README.md
│   ├── NIMBLE_LLM_CALLER_MIGRATION_GUIDE.md
│   ├── PHYSICAL_SPECS_README.md
│   ├── PIPELINE_CONFIGURATION_FIXES_SUMMARY.md
│   ├── PIPELINE_FIXES_FINAL_SUMMARY.md
│   ├── PROMPT_LOADING_LOGGING_SUMMARY.md
│   ├── PROMPT_MODERNIZATION_GUIDE.md
│   ├── REAL_LLM_INTEGRATION_SUMMARY.md
│   ├── REGRESSION_FIXES_SUMMARY.md
│   ├── RUNAWAY_LOOP_FIXES_SUMMARY.md
│   ├── STREAMLIT_FIXES_SUMMARY.md
│   ├── STREAMLIT_FORM_FIX_SUMMARY.md
│   ├── STREAMLIT_UI_GUIDE.md
│   ├── SUCCESS_MESSAGE_GUARANTEE_IMPLEMENTATION.md
│   ├── SUCCESS_MESSAGE_IMPLEMENTATION.md
│   ├── SUMMARY_OF_CHANGES.md
│   ├── TASK_9_IMPLEMENTATION_SUMMARY.md
│   ├── TESTING_README.md
│   ├── TOURNAMENT_ENGINE_FIX_SUMMARY.md
│   ├── TRANSFORMATION_CLI_GUIDE.md
│   ├── TROUBLESHOOTING_GUIDE.md
│   ├── TYPOGRAPHY_FORMATTING_EXAMPLES.md
│   ├── UNIVERSAL_WORKFLOW_INTERFACE_GUIDE.md
│   ├── VERIFICATION_LOAD_FILE_FIX_SUMMARY.md
│   ├── XYNAPSE_TRANCHE_1_SUMMARY.md
│   ├── api
│   │   ├── ai_coding_guidelines_codexes_factory.md
│   │   └── current_system_design.md
│   ├── assessments

│   ├── changelog

│   ├── configuration
│   │   └── lsi_configuration_system_documentation.md
│   ├── development
│   │   ├── BIBLIOGRAPHY_LOCKED.md
│   │   ├── interior_fixes.md
│   │   └── streamlit_ui_module.md
│   ├── guides

│   ├── misc
│   │   ├── sponsors.md
│   │   └── test_markdown.md
│   ├── notes
│   │   ├── assessment_plan_catalog.md
│   │   ├── assessment_plan_covers.md
│   │   ├── assessment_plan_llm.md
│   │   ├── assessment_plan_lsi.md
│   │   ├── assessment_plan_prepress.md
│   │   ├── project_status_per_gemini.md
│   │   ├── punch_sheet3.md
│   │   ├── todos.md
│   │   └── tranche24_notes.md
│   ├── readme
│   │   ├── codexes_factory_ai_assisted_publishing_platform_v32.md
│   │   ├── snapshots_directory.md
│   │   └── tools_directory.md
│   ├── resources
│   │   ├── Autonomous_Book_Publisher.md
│   │   ├── FredTJaneAIInterview.md
│   │   ├── KDP_core_metadata.md
│   │   ├── KDP_metadata.md
│   │   ├── KDP_series_metadata.md
│   │   ├── Nimble_Authors_In_The_News.md
│   │   ├── StyleGuide.md
│   │   ├── about_authorship.md
│   │   ├── about_fred.md
│   │   ├── about_message.md
│   │   ├── about_nimble.md
│   │   ├── annotated_bibliography_introduction.md
│   │   ├── codex2tools.md
│   │   ├── contents.md
│   │   ├── documentation.md
│   │   ├── due_diligence.md
│   │   ├── faq.md
│   │   ├── forthcoming.md
│   │   ├── kolb_3chapters.md
│   │   ├── locations.md
│   │   ├── longform_prospectus.md
│   │   ├── lorem_ipsum.md
│   │   ├── nimble_books_color_font_schemes.md
│   │   ├── pagekicker_manifesto.md
│   │   ├── reduce-processing-to-dos.md
│   │   ├── sidebar_message.md
│   │   ├── testtable.md
│   │   └── titivillus_cast.md
│   ├── specifications

│   ├── summaries

│   ├── tale.tex
│   ├── testing
│   │   ├── example_lsi_csv_outputs.md
│   │   └── test_logging_summary.md
│   ├── troubleshooting

│   └── tutorials

├── example_idea.json
├── example_idea_transformed.json
├── example_schedule.csv
├── example_schedule.json
├── examples
│   ├── configuration_unification_demo.py
│   ├── isbn_rebuild_integration.py
│   ├── logging_configuration_example.py
│   ├── schedule_import_example.py
│   └── success_message_example.py
├── exports
│   ├── exported_config_20250802_232442.json
│   ├── exported_config_20250802_234244.json
│   ├── exported_config_20250802_235351.json
│   └── exported_config_20250803_051207.json
├── fonts
│   └── BerkshireSwash-Regular.ttf
├── ftp2lsi

├── full_activation.sh
├── generate_lsi_csv.py
├── generate_lsi_field_report.py
├── ideation_app.py
├── imprints
│   ├── 4q2025.csv
│   ├── admin
│   │   ├── books.csv
│   │   ├── data
│   │   │   └── books.csv
│   │   ├── logo_directives.txt
│   │   ├── prompts
│   │   │   └── prompts.json
│   │   ├── prompts.json
│   │   └── templates
│   │       ├── cover_template.tex
│   │       └── template.tex
│   ├── books.csv
│   ├── jp_cross
│   │   ├── data

│   │   ├── prompts
│   │   │   └── prompts.json
│   │   └── templates

│   ├── preprocess_korean.csv
│   ├── text_hip_global
│   │   ├── __pycache__
│   │   │   └── prepress.cpython-312.pyc
│   │   ├── cover_template.tex
│   │   ├── dotgrid.png
│   │   ├── family.csv
│   │   ├── prepress.py
│   │   ├── preprocess_korean.py
│   │   ├── prompts.json
│   │   ├── schedule.csv
│   │   ├── schedule_4Q2025.json
│   │   └── template.tex
│   └── xynapse_traces
│       ├── Book4.csv
│       ├── Book5.csv
│       ├── __pycache__
│       │   └── prepress.cpython-312.pyc
│       ├── books.csv
│       ├── cover_template.tex
│       ├── dotgrid.png
│       ├── family.csv
│       ├── family_schedule.json
│       ├── full.json
│       ├── korean_tex_processor.py
│       ├── prepress.py
│       ├── preprocess_korean.py
│       ├── prompts.json
│       ├── publishing_schedule.csv
│       ├── schedule.csv
│       ├── schedule_with_isbns.json
│       ├── template.tex
│       ├── verification_protocol.tex
│       └── writing_style.json
├── input

├── integrate_ideas
│   ├── progress_reports.log
│   └── src
│       ├── __pycache__
│       │   └── __init__.cpython-312.pyc
│       ├── ideas
│       │   ├── BookClasses
│       │   │   └── __pycache__
│       │   │       ├── BookIdea.cpython-312.pyc
│       │   │       ├── BookIdeaSet.cpython-312.pyc
│       │   │       ├── IdeaGeneratingMachine.cpython-312.pyc
│       │   │       ├── Model2BookIdeas.cpython-312.pyc
│       │   │       └── __init__.cpython-312.pyc
│       │   ├── PureIdeas
│       │   │   ├── __pycache__
│       │   │   │   ├── Idea.cpython-312.pyc
│       │   │   │   └── __init__.cpython-312.pyc
│       │   │   └── collection
│       │   │       └── __pycache__
│       │   │           └── idea_collector.cpython-312.pyc
│       │   ├── Tournament
│       │   │   └── __pycache__
│       │   │       ├── Tournament.cpython-312.pyc
│       │   │       └── run_tournament.cpython-312.pyc
│       │   ├── Transformers
│       │   │   └── __pycache__
│       │   │       ├── __init__.cpython-312.pyc
│       │   │       └── idea_transformer.cpython-312.pyc
│       │   ├── __pycache__
│       │   │   ├── IdeaBaseClasses.cpython-312.pyc
│       │   │   ├── IdeaUtilities.cpython-312.pyc
│       │   │   ├── IdeasUtilities.cpython-312.pyc
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   └── cli.cpython-312.pyc
│       │   ├── vibes
│       │   │   └── __pycache__
│       │   │       ├── Model2BookIdeas.cpython-312.pyc
│       │   │       ├── __init__.cpython-312.pyc
│       │   │       ├── vibe_oral_history_builder.cpython-312.pyc
│       │   │       ├── vibe_oral_history_utilities.cpython-312.pyc
│       │   │       └── vibe_writer.cpython-312.pyc
│       │   └── xai_specific_idea_tools

│       └── ideas.egg-info
│           ├── PKG-INFO
│           ├── SOURCES.txt
│           ├── dependency_links.txt
│           ├── requires.txt
│           └── top_level.txt
├── integrate_synthetic_readers
│   └── SyntheticReaders
│       ├── __pycache__
│       │   ├── HeadlesslySendBooks2ReaderPanels.cpython-310.pyc
│       │   ├── RatingUtilities.cpython-310.pyc
│       │   ├── ReaderPanels.cpython-310.pyc
│       │   └── __init__.cpython-310.pyc
│       └── gemini2syntheticreaders
│           └── __pycache__
│               ├── BookAnalysisPlan.cpython-310.pyc
│               ├── __init__.cpython-310.pyc
│               └── text2gemini.cpython-310.pyc
├── isbn_report.json
├── ivanhoes.json
├── ivanhoes.txt
├── ivanhoes_transformed.json
├── llm_interactions.jsonl
├── logs
│   ├── application.log
│   ├── batch_reports

│   ├── codexes_run_20250822_225240.log
│   ├── critical_message_validation_20250824_105751.json
│   ├── critical_message_validation_20250824_105804.json
│   ├── critical_message_validation_20250824_194611.json
│   ├── errors.log
│   ├── isbn_import.log
│   ├── lsi_generation
│   │   ├── lsi_gen_20250717_015848_6362c009.json
│   │   ├── lsi_gen_20250717_074121_314fc574.json
│   │   ├── lsi_gen_20250717_074136_3b47d661.json
│   │   ├── lsi_gen_20250720_023857_cda14df5b06d.json
│   │   ├── lsi_gen_20250720_043948_cda14df5b06d.json
│   │   ├── lsi_gen_20250728_135406_223351583df5.json
│   │   ├── lsi_gen_20250728_135443_223351583df5.json
│   │   ├── lsi_gen_20250728_140518_223351583df5.json
│   │   ├── lsi_gen_20250728_192415_223351583df5.json
│   │   ├── lsi_gen_20250731_033738_f5ea10cd.json
│   │   ├── lsi_gen_20250731_033810_812b331e.json
│   │   ├── lsi_gen_20250731_033823_0cfcd4ae.json
│   │   ├── lsi_gen_20250731_115538_ddfb8742.json
│   │   ├── lsi_gen_20250731_115809_ae864e34.json
│   │   ├── lsi_gen_20250731_120713_9a761e72.json
│   │   ├── lsi_gen_20250731_122034_456095ce.json
│   │   ├── lsi_gen_20250809_023813_52e8208a.json
│   │   └── lsi_generation.log
│   ├── performance_profile_results.json
│   ├── resource_organization.log
│   └── test_live_pipeline
│       ├── lsi_gen_20250728_234115_68daa38a.json
│       ├── lsi_gen_20250729_000145_612ac168.json
│       ├── lsi_gen_20250729_005250_887ec82d.json
│       ├── lsi_gen_20250729_010124_c2e02c4b.json
│       ├── lsi_gen_20250729_011403_f854bd82.json
│       ├── lsi_gen_20250729_011505_69f71fca.json
│       ├── lsi_gen_20250729_013716_ddb1aae6.json
│       ├── lsi_gen_20250729_013752_cfed94b7.json
│       ├── lsi_gen_20250729_021750_0d35e785.json
│       ├── lsi_gen_20250729_022126_1bab54b1.json
│       ├── lsi_gen_20250729_022356_07eeee9f.json
│       ├── lsi_gen_20250729_023523_0fa2b35c.json
│       ├── lsi_gen_20250729_023553_789cfeca.json
│       ├── lsi_gen_20250729_023614_2b4c4ee5.json
│       ├── lsi_gen_20250729_092627_cd12a7dc.json
│       ├── lsi_generation.log
│       └── test.log
├── manage_imprints.py
├── merged_schedule.csv
├── modernize_prompts.py
├── monitor_llm_responses.py
├── multistart_streamlit.py
├── notes_and_reports
│   ├── issues
│   ├── punch_list.csv
│   └── verify_list.txt
├── organize_resources.py
├── output
│   ├── alternative_format
│   │   ├── heritage_historical_fiction.json
│   │   ├── modern_minimalist_press.json
│   │   └── tech_tomorrow_publishing.json
│   ├── batch_index_20250811_222356.json
│   ├── batch_index_20250812_200809.json
│   ├── batch_processing

│   ├── error_report_imprint_ideas.json
│   ├── expanded_imprint.json
│   ├── expanded_imprint_real.json
│   ├── imprint_ideas
│   │   ├── ancient_scripts_&.json
│   │   ├── arcana_script.json
│   │   ├── art_&_form.json
│   │   ├── chrono-verse_press.json
│   │   ├── cognition_compass.json
│   │   ├── digital_echoes.json
│   │   ├── earth's_story.json
│   │   ├── global_fabric.json
│   │   ├── innovate_&_thrive.json
│   │   ├── mind_weave_stories.json
│   │   ├── mythos_&_machine.json
│   │   ├── shattered_horizons_fiction.json
│   │   ├── the_alchemist's_quill.json
│   │   └── veridian_narratives.json
│   ├── integration_test_results_20250719_093359.json
│   ├── llm_responses

│   ├── metadata
│   │   └── unknown_20250809_023813
│   │       ├── latest_llm_completions.json
│   │       ├── latest_llm_completions_.json
│   │       └── llm_completions__20250809_023813.json
│   ├── nimble_books

│   ├── reports
│   │   ├── field_report_9781234567890_20250720_152656.csv
│   │   ├── field_report_9781234567890_20250720_152656.html
│   │   ├── field_report_9781234567890_20250720_152656.json
│   │   ├── field_report_9781234567890_20250720_153138.csv
│   │   ├── field_report_9781234567890_20250720_153138.html
│   │   └── field_report_9781234567890_20250720_153138.json
│   ├── resources
│   │   └── cumulative.csv
│   ├── test_live_pipeline_lsi.csv
│   ├── text_hip_global_build
│   │   ├── covers
│   │   │   ├── The_Future_of_Space_Robotics_back_cover.png
│   │   │   ├── The_Future_of_Space_Robotics_cover_spread.pdf
│   │   │   ├── The_Future_of_Space_Robotics_cover_spread.png
│   │   │   └── The_Future_of_Space_Robotics_front_cover.png
│   │   ├── interior
│   │   │   └── The_Future_of_Space_Robotics_interior.pdf
│   │   ├── lsi_csv

│   │   ├── processed_json
│   │   │   ├── The_Future_of_Space_Robotics.json
│   │   │   └── The_Future_of_Space_Robotics.md
│   │   └── raw_json_responses
│   │       ├── The_Future_of_Space_Robotics_back_cover_text.txt
│   │       ├── The_Future_of_Space_Robotics_bibliographic_key_phrases.txt
│   │       ├── The_Future_of_Space_Robotics_bibliography_prompt.txt
│   │       ├── The_Future_of_Space_Robotics_custom_transcription_note_prompt.txt
│   │       ├── The_Future_of_Space_Robotics_gemini_get_basic_info.txt
│   │       ├── The_Future_of_Space_Robotics_imprint_quotes_prompt.txt
│   │       ├── The_Future_of_Space_Robotics_storefront_get_en_metadata.txt
│   │       ├── The_Future_of_Space_Robotics_storefront_get_en_motivation.txt
│   │       ├── The_Future_of_Space_Robotics_storefront_get_ko_metadata.txt
│   │       └── The_Future_of_Space_Robotics_storefront_get_ko_motivation.txt
│   ├── xynapse_traces_build
│   │   ├── covers
│   │   │   ├── 9781608884810-Perfect (3)-page001.eps
│   │   │   ├── 9781608884810_cover.eps
│   │   │   ├── 9781608884810_cover.pdf
│   │   │   ├── AI-Driven_Science_Speed_versus_Safety_back_cover.png
│   │   │   ├── AI-Driven_Science_Speed_versus_Safety_cover_spread.pdf
│   │   │   ├── AI-Driven_Science_Speed_versus_Safety_cover_spread.png
│   │   │   ├── AI-Driven_Science_Speed_versus_Safety_front_cover.png
│   │   │   ├── AI_Governance_Freedom_versus_Constraint_back_cover.png
│   │   │   ├── AI_Governance_Freedom_versus_Constraint_cover_spread.pdf
│   │   │   ├── AI_Governance_Freedom_versus_Constraint_cover_spread.png
│   │   │   ├── AI_Governance_Freedom_versus_Constraint_front_cover.png
│   │   │   ├── Family_Support_Data_versus_Intuition_back_cover.png
│   │   │   ├── Family_Support_Data_versus_Intuition_cover_spread.pdf
│   │   │   ├── Family_Support_Data_versus_Intuition_cover_spread.png
│   │   │   ├── Family_Support_Data_versus_Intuition_front_cover.png
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity_back_cover.png
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity_cover_spread.pdf
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity_cover_spread.png
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity_front_cover.png
│   │   │   ├── Global_Renewables_back_cover.png
│   │   │   ├── Global_Renewables_cover_spread.pdf
│   │   │   ├── Global_Renewables_cover_spread.png
│   │   │   ├── Global_Renewables_front_cover.png
│   │   │   ├── Glossary_Fix_Verification_back_cover.png
│   │   │   ├── Glossary_Fix_Verification_cover_spread.pdf
│   │   │   ├── Glossary_Fix_Verification_cover_spread.png
│   │   │   ├── Glossary_Fix_Verification_front_cover.png
│   │   │   ├── Glossary_Formatting_Test_back_cover.png
│   │   │   ├── Glossary_Formatting_Test_cover_spread.pdf
│   │   │   ├── Glossary_Formatting_Test_cover_spread.png
│   │   │   ├── Glossary_Formatting_Test_front_cover.png
│   │   │   ├── Internet_for_All_Inclusion_versus_Barriers_back_cover.png
│   │   │   ├── Internet_for_All_Inclusion_versus_Barriers_cover_spread.pdf
│   │   │   ├── Internet_for_All_Inclusion_versus_Barriers_cover_spread.png
│   │   │   ├── Internet_for_All_Inclusion_versus_Barriers_front_cover.png
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction_back_cover.png
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction_cover_spread.pdf
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction_cover_spread.png
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction_front_cover.png
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight_back_cover.png
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight_cover_spread.pdf
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight_cover_spread.png
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight_front_cover.png
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_back_cover.png
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_cover_spread.pdf
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_cover_spread.png
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_front_cover.png
│   │   │   ├── Martian_Self-Reliance_back_cover.png
│   │   │   ├── Martian_Self-Reliance_cover_spread.pdf
│   │   │   ├── Martian_Self-Reliance_cover_spread.png
│   │   │   ├── Martian_Self-Reliance_front_cover.png
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency_back_cover.png
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency_cover_spread.pdf
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency_cover_spread.png
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency_front_cover.png
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity_back_cover.png
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity_cover_spread.pdf
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity_cover_spread.png
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity_front_cover.png
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance_back_cover.png
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance_cover_spread.pdf
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance_cover_spread.png
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance_front_cover.png
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight_back_cover.png
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight_cover_spread.pdf
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight_cover_spread.png
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight_front_cover.png
│   │   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility_back_cover.png
│   │   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility_cover_spread.pdf
│   │   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility_cover_spread.png
│   │   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility_front_cover.png
│   │   │   ├── The_Beauty_of_Astrophysics_back_cover.png
│   │   │   ├── The_Beauty_of_Astrophysics_cover_spread.pdf
│   │   │   ├── The_Beauty_of_Astrophysics_cover_spread.png
│   │   │   ├── The_Beauty_of_Astrophysics_front_cover.png
│   │   │   ├── The_Future_of_Geoinformatics_back_cover.png
│   │   │   ├── The_Future_of_Geoinformatics_cover_spread.pdf
│   │   │   ├── The_Future_of_Geoinformatics_cover_spread.png
│   │   │   ├── The_Future_of_Geoinformatics_front_cover.png
│   │   │   ├── Underground_Planning_Resilience_versus_Accessibility_back_cover.png
│   │   │   ├── Underground_Planning_Resilience_versus_Accessibility_cover_spread.pdf
│   │   │   ├── Underground_Planning_Resilience_versus_Accessibility_cover_spread.png
│   │   │   └── Underground_Planning_Resilience_versus_Accessibility_front_cover.png
│   │   ├── interior
│   │   │   ├── 9781608884810_interior.pdf
│   │   │   ├── 9781608884810_interior.ps
│   │   │   ├── AI-Driven_Science_Speed_versus_Safety_interior.pdf
│   │   │   ├── AI_Governance_Freedom_versus_Constraint_interior.pdf
│   │   │   ├── Family_Support_Data_versus_Intuition_interior.pdf
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity_interior.pdf
│   │   │   ├── Global_Renewables_interior.pdf
│   │   │   ├── Glossary_Fix_Verification_interior.pdf
│   │   │   ├── Glossary_Formatting_Test_interior.pdf
│   │   │   ├── Internet_for_All_Inclusion_versus_Barriers_interior.pdf
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction_interior.pdf
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight_interior.pdf
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_interior.pdf
│   │   │   ├── Martian_Self-Reliance_interior.pdf
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency_interior.pdf
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity_interior.pdf
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance_interior.pdf
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight_interior.pdf
│   │   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility_interior.pdf
│   │   │   ├── The_Beauty_of_Astrophysics_interior.pdf
│   │   │   ├── The_Future_of_Geoinformatics_interior.pdf
│   │   │   └── Underground_Planning_Resilience_versus_Accessibility_interior.pdf
│   │   ├── lsi_csv
│   │   │   ├── logs
│   │   │   │   ├── lsi_gen_20250805_012126_c25bf334.json
│   │   │   │   ├── lsi_gen_20250805_024237_7642002b.json
│   │   │   │   ├── lsi_gen_20250805_184406_d2da73f5.json
│   │   │   │   ├── lsi_gen_20250805_214055_530cd0cd.json
│   │   │   │   ├── lsi_gen_20250805_233735_3a48b61f.json
│   │   │   │   ├── lsi_gen_20250806_010711_730a479f.json
│   │   │   │   ├── lsi_gen_20250806_012012_83fcf936.json
│   │   │   │   ├── lsi_gen_20250806_013357_7a0c85fb.json
│   │   │   │   ├── lsi_gen_20250806_020340_08730968.json
│   │   │   │   ├── lsi_gen_20250806_024919_8a99934b.json
│   │   │   │   ├── lsi_gen_20250806_104615_d3481060.json
│   │   │   │   ├── lsi_gen_20250806_172348_7f4528d0.json
│   │   │   │   ├── lsi_gen_20250806_201533_1fb795e4.json
│   │   │   │   ├── lsi_gen_20250806_203037_6b522e85.json
│   │   │   │   ├── lsi_gen_20250806_215111_c82e4265.json
│   │   │   │   ├── lsi_gen_20250806_225826_b808fce9.json
│   │   │   │   ├── lsi_gen_20250807_002310_903eacc9.json
│   │   │   │   ├── lsi_gen_20250813_041929_b80dcb77.json
│   │   │   │   ├── lsi_gen_20250818_202941_41af6fa1.json
│   │   │   │   ├── lsi_gen_20250818_210317_384fd9b7.json
│   │   │   │   ├── lsi_gen_20250819_082441_e2dd7bd8.json
│   │   │   │   ├── lsi_gen_20250822_184230_078b4003.json
│   │   │   │   ├── lsi_gen_20250822_191005_cbe04b2d.json
│   │   │   │   ├── lsi_gen_20250823_045720_0d70e729.json
│   │   │   │   ├── lsi_gen_20250823_080608_8507e6b1.json
│   │   │   │   ├── lsi_gen_20250823_082841_f9d0d799.json
│   │   │   │   ├── lsi_gen_20250823_092207_acaabf2b.json
│   │   │   │   ├── lsi_gen_20250823_095347_dbea56bd.json
│   │   │   │   ├── lsi_gen_20250823_141122_e32e2a16.json
│   │   │   │   ├── lsi_gen_20250823_195753_e89649e4.json
│   │   │   │   ├── lsi_gen_20250824_032020_803d5b94.json
│   │   │   │   ├── lsi_gen_20250824_175624_f5a1f100.json
│   │   │   │   ├── lsi_gen_20250824_194315_ccb6ccb3.json
│   │   │   │   ├── lsi_gen_20250824_204553_fb7c2524.json
│   │   │   │   ├── lsi_gen_20250824_211844_bcb6b60c.json
│   │   │   │   ├── lsi_gen_20250824_213959_c92cc21c.json
│   │   │   │   ├── lsi_gen_20250825_092240_df4ec736.json
│   │   │   │   ├── lsi_gen_20250825_105843_74c5254a.json
│   │   │   │   ├── lsi_gen_20250825_142523_99c5f3ef.json
│   │   │   │   ├── lsi_gen_20250825_213435_05f57302.json
│   │   │   │   └── lsi_generation.log
│   │   │   └── xynapse_traces_batch_LSI.csv
│   │   ├── metadata
│   │   │   ├── latest_llm_completions.json
│   │   │   ├── latest_llm_completions_.json
│   │   │   ├── latest_llm_completions_978-0-123456-78-9.json
│   │   │   ├── llm_completions_978-0-123456-78-9_20250806_010711.json
│   │   │   ├── llm_completions__20250805_012126.json
│   │   │   ├── llm_completions__20250805_024237.json
│   │   │   ├── llm_completions__20250805_184406.json
│   │   │   ├── llm_completions__20250805_214055.json
│   │   │   ├── llm_completions__20250805_233735.json
│   │   │   ├── llm_completions__20250806_012012.json
│   │   │   ├── llm_completions__20250806_013357.json
│   │   │   ├── llm_completions__20250806_024919.json
│   │   │   ├── llm_completions__20250806_104615.json
│   │   │   ├── llm_completions__20250806_172348.json
│   │   │   ├── llm_completions__20250806_201533.json
│   │   │   ├── llm_completions__20250806_203037.json
│   │   │   ├── llm_completions__20250806_215111.json
│   │   │   ├── llm_completions__20250806_225826.json
│   │   │   ├── llm_completions__20250806_234338.json
│   │   │   ├── llm_completions__20250807_000249.json
│   │   │   ├── llm_completions__20250807_002310.json
│   │   │   ├── llm_completions__20250813_034622.json
│   │   │   ├── llm_completions__20250813_040352.json
│   │   │   ├── llm_completions__20250813_041929.json
│   │   │   ├── llm_completions__20250818_202941.json
│   │   │   └── llm_completions__20250818_210317.json
│   │   ├── processed_json
│   │   │   ├── AI-Driven_Science_Speed_versus_Safety.json
│   │   │   ├── AI_Governance_Freedom_versus_Constraint.json
│   │   │   ├── AI_Governance_Freedom_versus_Constraint.md
│   │   │   ├── AI_Precision_Accuracy_versus_Error.json
│   │   │   ├── Battery_Revolution_Innovation_versus_Constraints.json
│   │   │   ├── Birth_Rate_Boost_Policy_versus_Freedom.json
│   │   │   ├── Cognitive_Upgrades_Necessity_versus_Luxury.json
│   │   │   ├── Family_Support_Data_versus_Intuition.json
│   │   │   ├── Family_Support_Data_versus_Intuition.md
│   │   │   ├── Fertility_Optimization_Technology_versus_Nature.json
│   │   │   ├── Free_Speech_Platforms_Openness_versus_Regulation.json
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity.json
│   │   │   ├── Global_Renewables_Scale_versus_Scarcity.md
│   │   │   ├── Industry_Shifts_Innovation_versus_Instability.json
│   │   │   ├── Internet_for_All_Inclusion_versus_Barriers.json
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction.json
│   │   │   ├── Knowledge_Access_Freedom_versus_Restriction.md
│   │   │   ├── Knowledge_Networks_Cohesion_versus_Division.json
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight.json
│   │   │   ├── Mars_Governance_Autonomy_versus_Oversight.md
│   │   │   ├── Martian_Commerce_Local_versus_Interplanetary.json
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support.json
│   │   │   ├── Martian_Self-Reliance_Isolation_versus_Earth_Support.md
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency.json
│   │   │   ├── Mind-Machine_Fusion_Liberation_versus_Dependency.md
│   │   │   ├── Open_Government_Transparency_versus_Security.json
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity.json
│   │   │   ├── Policy_Automation_Efficiency_versus_Equity.md
│   │   │   ├── Satellite_Networks_Durability_versus_Risks.json
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance.json
│   │   │   ├── Solar_Expansion_Dominance_versus_Balance.md
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight.json
│   │   │   ├── Streamlined_Governance_Agility_versus_Oversight.md
│   │   │   ├── Subterranean_Cities_Efficiency_versus_Feasibility.json
│   │   │   ├── Tunnel_Viability_Speed_versus_Stability.json
│   │   │   ├── Underground_Planning_Resilience_versus_Accessibility.json
│   │   │   ├── Underground_Planning_Resilience_versus_Accessibility.md
│   │   │   └── Visionary_Drive_Passion_versus_Peril.json
│   │   └── raw_json_responses
│   │       ├── AI-Driven_Science_Speed_versus_Safety_back_cover_text.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_bibliographic_key_phrases.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_bibliography_prompt.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_custom_transcription_note_prompt.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_gemini_get_basic_info.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_imprint_quotes_prompt.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_en_metadata.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_en_motivation.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_ko_metadata.txt
│   │       ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_ko_motivation.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_back_cover_text.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_bibliographic_key_phrases.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_bibliography_prompt.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_custom_transcription_note_prompt.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_gemini_get_basic_info.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_imprint_quotes_prompt.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_storefront_get_en_metadata.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_storefront_get_en_motivation.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_storefront_get_ko_metadata.txt
│   │       ├── AI_Governance_Freedom_versus_Constraint_storefront_get_ko_motivation.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_back_cover_text.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_bibliographic_key_phrases.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_bibliography_prompt.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_custom_transcription_note_prompt.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_gemini_get_basic_info.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_imprint_quotes_prompt.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_storefront_get_en_metadata.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_storefront_get_en_motivation.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_storefront_get_ko_metadata.txt
│   │       ├── AI_Precision_Accuracy_versus_Error_storefront_get_ko_motivation.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_back_cover_text.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_bibliographic_key_phrases.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_bibliography_prompt.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_custom_transcription_note_prompt.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_gemini_get_basic_info.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_imprint_quotes_prompt.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_storefront_get_en_metadata.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_storefront_get_en_motivation.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_storefront_get_ko_metadata.txt
│   │       ├── Battery_Revolution_Innovation_versus_Constraints_storefront_get_ko_motivation.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_back_cover_text.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_bibliographic_key_phrases.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_bibliography_prompt.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_custom_transcription_note_prompt.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_gemini_get_basic_info.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_imprint_quotes_prompt.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_storefront_get_en_metadata.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_storefront_get_en_motivation.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_storefront_get_ko_metadata.txt
│   │       ├── Birth_Rate_Boost_Policy_versus_Freedom_storefront_get_ko_motivation.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_back_cover_text.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_bibliographic_key_phrases.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_bibliography_prompt.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_custom_transcription_note_prompt.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_gemini_get_basic_info.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_imprint_quotes_prompt.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_storefront_get_en_metadata.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_storefront_get_en_motivation.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_storefront_get_ko_metadata.txt
│   │       ├── Cognitive_Upgrades_Necessity_versus_Luxury_storefront_get_ko_motivation.txt
│   │       ├── Family_Support_Data_versus_Intuition_back_cover_text.txt
│   │       ├── Family_Support_Data_versus_Intuition_bibliographic_key_phrases.txt
│   │       ├── Family_Support_Data_versus_Intuition_bibliography_prompt.txt
│   │       ├── Family_Support_Data_versus_Intuition_custom_transcription_note_prompt.txt
│   │       ├── Family_Support_Data_versus_Intuition_gemini_get_basic_info.txt
│   │       ├── Family_Support_Data_versus_Intuition_imprint_quotes_prompt.txt
│   │       ├── Family_Support_Data_versus_Intuition_storefront_get_en_metadata.txt
│   │       ├── Family_Support_Data_versus_Intuition_storefront_get_en_motivation.txt
│   │       ├── Family_Support_Data_versus_Intuition_storefront_get_ko_metadata.txt
│   │       ├── Family_Support_Data_versus_Intuition_storefront_get_ko_motivation.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_back_cover_text.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_bibliographic_key_phrases.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_bibliography_prompt.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_custom_transcription_note_prompt.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_gemini_get_basic_info.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_imprint_quotes_prompt.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_storefront_get_en_metadata.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_storefront_get_en_motivation.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_storefront_get_ko_metadata.txt
│   │       ├── Fertility_Optimization_Technology_versus_Nature_storefront_get_ko_motivation.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_back_cover_text.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_bibliographic_key_phrases.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_bibliography_prompt.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_custom_transcription_note_prompt.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_gemini_get_basic_info.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_imprint_quotes_prompt.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_storefront_get_en_metadata.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_storefront_get_en_motivation.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_storefront_get_ko_metadata.txt
│   │       ├── Free_Speech_Platforms_Openness_versus_Regulation_storefront_get_ko_motivation.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_back_cover_text.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_bibliographic_key_phrases.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_bibliography_prompt.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_custom_transcription_note_prompt.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_gemini_get_basic_info.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_imprint_quotes_prompt.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_storefront_get_en_metadata.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_storefront_get_en_motivation.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_storefront_get_ko_metadata.txt
│   │       ├── Global_Renewables_Scale_versus_Scarcity_storefront_get_ko_motivation.txt
│   │       ├── Global_Renewables_back_cover_text.txt
│   │       ├── Global_Renewables_bibliographic_key_phrases.txt
│   │       ├── Global_Renewables_bibliography_prompt.txt
│   │       ├── Global_Renewables_custom_transcription_note_prompt.txt
│   │       ├── Global_Renewables_gemini_get_basic_info.txt
│   │       ├── Global_Renewables_imprint_quotes_prompt.txt
│   │       ├── Global_Renewables_storefront_get_en_metadata.txt
│   │       ├── Global_Renewables_storefront_get_en_motivation.txt
│   │       ├── Global_Renewables_storefront_get_ko_metadata.txt
│   │       ├── Global_Renewables_storefront_get_ko_motivation.txt
│   │       ├── Glossary_Fix_Verification_back_cover_text.txt
│   │       ├── Glossary_Fix_Verification_bibliographic_key_phrases.txt
│   │       ├── Glossary_Fix_Verification_bibliography_prompt.txt
│   │       ├── Glossary_Fix_Verification_custom_transcription_note_prompt.txt
│   │       ├── Glossary_Fix_Verification_gemini_get_basic_info.txt
│   │       ├── Glossary_Fix_Verification_imprint_quotes_prompt.txt
│   │       ├── Glossary_Fix_Verification_storefront_get_en_metadata.txt
│   │       ├── Glossary_Fix_Verification_storefront_get_en_motivation.txt
│   │       ├── Glossary_Fix_Verification_storefront_get_ko_metadata.txt
│   │       ├── Glossary_Fix_Verification_storefront_get_ko_motivation.txt
│   │       ├── Glossary_Formatting_Test_back_cover_text.txt
│   │       ├── Glossary_Formatting_Test_bibliographic_key_phrases.txt
│   │       ├── Glossary_Formatting_Test_bibliography_prompt.txt
│   │       ├── Glossary_Formatting_Test_custom_transcription_note_prompt.txt
│   │       ├── Glossary_Formatting_Test_gemini_get_basic_info.txt
│   │       ├── Glossary_Formatting_Test_imprint_quotes_prompt.txt
│   │       ├── Glossary_Formatting_Test_storefront_get_en_metadata.txt
│   │       ├── Glossary_Formatting_Test_storefront_get_en_motivation.txt
│   │       ├── Glossary_Formatting_Test_storefront_get_ko_metadata.txt
│   │       ├── Glossary_Formatting_Test_storefront_get_ko_motivation.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_back_cover_text.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_bibliographic_key_phrases.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_bibliography_prompt.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_custom_transcription_note_prompt.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_gemini_get_basic_info.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_imprint_quotes_prompt.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_storefront_get_en_metadata.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_storefront_get_en_motivation.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_storefront_get_ko_metadata.txt
│   │       ├── Industry_Shifts_Innovation_versus_Instability_storefront_get_ko_motivation.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_back_cover_text.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_bibliographic_key_phrases.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_bibliography_prompt.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_custom_transcription_note_prompt.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_gemini_get_basic_info.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_imprint_quotes_prompt.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_storefront_get_en_metadata.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_storefront_get_en_motivation.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_storefront_get_ko_metadata.txt
│   │       ├── Internet_for_All_Inclusion_versus_Barriers_storefront_get_ko_motivation.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_back_cover_text.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_bibliographic_key_phrases.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_bibliography_prompt.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_custom_transcription_note_prompt.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_gemini_get_basic_info.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_imprint_quotes_prompt.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_storefront_get_en_metadata.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_storefront_get_en_motivation.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_storefront_get_ko_metadata.txt
│   │       ├── Knowledge_Access_Freedom_versus_Restriction_storefront_get_ko_motivation.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_back_cover_text.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_bibliographic_key_phrases.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_bibliography_prompt.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_custom_transcription_note_prompt.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_gemini_get_basic_info.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_imprint_quotes_prompt.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_storefront_get_en_metadata.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_storefront_get_en_motivation.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_storefront_get_ko_metadata.txt
│   │       ├── Knowledge_Networks_Cohesion_versus_Division_storefront_get_ko_motivation.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_back_cover_text.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_bibliographic_key_phrases.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_bibliography_prompt.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_custom_transcription_note_prompt.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_gemini_get_basic_info.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_imprint_quotes_prompt.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_storefront_get_en_metadata.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_storefront_get_en_motivation.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_storefront_get_ko_metadata.txt
│   │       ├── Mars_Governance_Autonomy_versus_Oversight_storefront_get_ko_motivation.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_back_cover_text.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_bibliographic_key_phrases.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_bibliography_prompt.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_custom_transcription_note_prompt.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_gemini_get_basic_info.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_imprint_quotes_prompt.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_storefront_get_en_metadata.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_storefront_get_en_motivation.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_storefront_get_ko_metadata.txt
│   │       ├── Martian_Commerce_Local_versus_Interplanetary_storefront_get_ko_motivation.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_back_cover_text.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_bibliographic_key_phrases.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_bibliography_prompt.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_custom_transcription_note_prompt.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_gemini_get_basic_info.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_imprint_quotes_prompt.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_storefront_get_en_metadata.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_storefront_get_en_motivation.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_storefront_get_ko_metadata.txt
│   │       ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_storefront_get_ko_motivation.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_back_cover_text.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_bibliographic_key_phrases.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_bibliography_prompt.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_custom_transcription_note_prompt.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_gemini_get_basic_info.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_imprint_quotes_prompt.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_storefront_get_en_metadata.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_storefront_get_en_motivation.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_storefront_get_ko_metadata.txt
│   │       ├── Mind-Machine_Fusion_Liberation_versus_Dependency_storefront_get_ko_motivation.txt
│   │       ├── Open_Government_Transparency_versus_Security_back_cover_text.txt
│   │       ├── Open_Government_Transparency_versus_Security_bibliographic_key_phrases.txt
│   │       ├── Open_Government_Transparency_versus_Security_bibliography_prompt.txt
│   │       ├── Open_Government_Transparency_versus_Security_custom_transcription_note_prompt.txt
│   │       ├── Open_Government_Transparency_versus_Security_gemini_get_basic_info.txt
│   │       ├── Open_Government_Transparency_versus_Security_imprint_quotes_prompt.txt
│   │       ├── Open_Government_Transparency_versus_Security_storefront_get_en_metadata.txt
│   │       ├── Open_Government_Transparency_versus_Security_storefront_get_en_motivation.txt
│   │       ├── Open_Government_Transparency_versus_Security_storefront_get_ko_metadata.txt
│   │       ├── Open_Government_Transparency_versus_Security_storefront_get_ko_motivation.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_back_cover_text.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_bibliographic_key_phrases.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_bibliography_prompt.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_custom_transcription_note_prompt.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_gemini_get_basic_info.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_imprint_quotes_prompt.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_storefront_get_en_metadata.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_storefront_get_en_motivation.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_storefront_get_ko_metadata.txt
│   │       ├── Policy_Automation_Efficiency_versus_Equity_storefront_get_ko_motivation.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_back_cover_text.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_bibliographic_key_phrases.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_bibliography_prompt.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_custom_transcription_note_prompt.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_gemini_get_basic_info.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_imprint_quotes_prompt.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_storefront_get_en_metadata.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_storefront_get_en_motivation.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_storefront_get_ko_metadata.txt
│   │       ├── Satellite_Networks_Durability_versus_Risks_storefront_get_ko_motivation.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_back_cover_text.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_bibliographic_key_phrases.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_bibliography_prompt.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_custom_transcription_note_prompt.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_gemini_get_basic_info.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_imprint_quotes_prompt.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_storefront_get_en_metadata.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_storefront_get_en_motivation.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_storefront_get_ko_metadata.txt
│   │       ├── Solar_Expansion_Dominance_versus_Balance_storefront_get_ko_motivation.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_back_cover_text.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_bibliographic_key_phrases.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_bibliography_prompt.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_custom_transcription_note_prompt.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_gemini_get_basic_info.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_imprint_quotes_prompt.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_storefront_get_en_metadata.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_storefront_get_en_motivation.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_storefront_get_ko_metadata.txt
│   │       ├── Streamlined_Governance_Agility_versus_Oversight_storefront_get_ko_motivation.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_back_cover_text.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_bibliographic_key_phrases.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_bibliography_prompt.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_custom_transcription_note_prompt.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_gemini_get_basic_info.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_imprint_quotes_prompt.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_storefront_get_en_metadata.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_storefront_get_en_motivation.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_storefront_get_ko_metadata.txt
│   │       ├── Subterranean_Cities_Efficiency_versus_Feasibility_storefront_get_ko_motivation.txt
│   │       ├── The_Beauty_of_Astrophysics_back_cover_text.txt
│   │       ├── The_Beauty_of_Astrophysics_bibliographic_key_phrases.txt
│   │       ├── The_Beauty_of_Astrophysics_bibliography_prompt.txt
│   │       ├── The_Beauty_of_Astrophysics_custom_transcription_note_prompt.txt
│   │       ├── The_Beauty_of_Astrophysics_gemini_get_basic_info.txt
│   │       ├── The_Beauty_of_Astrophysics_imprint_quotes_prompt.txt
│   │       ├── The_Beauty_of_Astrophysics_storefront_get_en_metadata.txt
│   │       ├── The_Beauty_of_Astrophysics_storefront_get_en_motivation.txt
│   │       ├── The_Beauty_of_Astrophysics_storefront_get_ko_metadata.txt
│   │       ├── The_Beauty_of_Astrophysics_storefront_get_ko_motivation.txt
│   │       ├── The_Future_of_Geoinformatics_back_cover_text.txt
│   │       ├── The_Future_of_Geoinformatics_bibliographic_key_phrases.txt
│   │       ├── The_Future_of_Geoinformatics_bibliography_prompt.txt
│   │       ├── The_Future_of_Geoinformatics_custom_transcription_note_prompt.txt
│   │       ├── The_Future_of_Geoinformatics_gemini_get_basic_info.txt
│   │       ├── The_Future_of_Geoinformatics_imprint_quotes_prompt.txt
│   │       ├── The_Future_of_Geoinformatics_storefront_get_en_metadata.txt
│   │       ├── The_Future_of_Geoinformatics_storefront_get_en_motivation.txt
│   │       ├── The_Future_of_Geoinformatics_storefront_get_ko_metadata.txt
│   │       ├── The_Future_of_Geoinformatics_storefront_get_ko_motivation.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_back_cover_text.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_bibliographic_key_phrases.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_bibliography_prompt.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_custom_transcription_note_prompt.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_gemini_get_basic_info.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_imprint_quotes_prompt.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_storefront_get_en_metadata.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_storefront_get_en_motivation.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_storefront_get_ko_metadata.txt
│   │       ├── Tunnel_Viability_Speed_versus_Stability_storefront_get_ko_motivation.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_back_cover_text.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_bibliographic_key_phrases.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_bibliography_prompt.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_custom_transcription_note_prompt.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_gemini_get_basic_info.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_imprint_quotes_prompt.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_storefront_get_en_metadata.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_storefront_get_en_motivation.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_storefront_get_ko_metadata.txt
│   │       ├── Underground_Planning_Resilience_versus_Accessibility_storefront_get_ko_motivation.txt
│   │       ├── Untitled_Book_imprint_quotes_prompt.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_back_cover_text.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_bibliographic_key_phrases.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_bibliography_prompt.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_custom_transcription_note_prompt.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_gemini_get_basic_info.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_imprint_quotes_prompt.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_storefront_get_en_metadata.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_storefront_get_en_motivation.txt
│   │       ├── Visionary_Drive_Passion_versus_Peril_storefront_get_ko_metadata.txt
│   │       └── Visionary_Drive_Passion_versus_Peril_storefront_get_ko_motivation.txt
│   ├── xynapse_traces_ideas
│   │   ├── 038c37fb
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 05c671f3
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 0d198e4e
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 214c8f8e
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 2a18a686
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 39e98a11
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 3d9dd429
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 47c4e7f3
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 4a2ce737
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 4e968a76
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 4f77b667
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 5058ed00
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 536b3481
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 647d720f
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 64f2f70b
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 6ce114fd
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 779df16d
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 7c1b2b8d
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 7df8f81c
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 7fd7d7e3
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 8490d119
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 8f42fa52
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── 9cf7fd20
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── a93e2ca9
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── aa3eb548
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── af366e71
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── b75e9593
│   │   │   ├── generated_book_ideas.csv
│   │   │   └── generated_book_ideas.json
│   │   ├── b7ce0081
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── ba4b45fd
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── c10b82bd
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── cb9e5126
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── cc24b0bf
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── cddb768b
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── cedb6755
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── d5f23d70
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── e24ee0dc
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── e34d0e52
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── e599fa0c
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── e6bbd2ea
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── efc8ea1c
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── f3a1a076
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── f69dd4f5
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── f7008239
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── fbd2b618
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   ├── fd1b87a3
│   │   │   ├── generated_book_ideas.csv
│   │   │   ├── generated_book_ideas.json
│   │   │   ├── tournament_matches.json
│   │   │   └── tournament_summary.json
│   │   └── resources
│   │       ├── cumulative.csv
│   │       └── progress_reports.log
│   └── xynapse_traces_test_run
│       ├── 20250729_2056_books.csv
│       ├── 20250729_2110_books.csv
│       ├── 20250730_0928_books.csv
│       ├── 20250730_1614_books.csv
│       ├── 20250801_2204_books.csv
│       ├── catalog.csv
│       ├── covers
│       │   ├── AI-Driven_Science_Speed_versus_Safety_back_cover.png
│       │   ├── AI-Driven_Science_Speed_versus_Safety_cover_spread.pdf
│       │   ├── AI-Driven_Science_Speed_versus_Safety_cover_spread.png
│       │   ├── AI-Driven_Science_Speed_versus_Safety_front_cover.png
│       │   ├── Global_Renewables_Scale_versus_Scarcity_back_cover.png
│       │   ├── Global_Renewables_Scale_versus_Scarcity_cover_spread.pdf
│       │   ├── Global_Renewables_Scale_versus_Scarcity_cover_spread.png
│       │   └── Global_Renewables_Scale_versus_Scarcity_front_cover.png
│       ├── cumulative.csv
│       ├── interior
│       │   ├── AI-Driven_Science_Speed_versus_Safety_interior.pdf
│       │   └── Global_Renewables_Scale_versus_Scarcity_interior.pdf
│       ├── lsi_csv
│       │   ├── logs
│       │   │   ├── lsi_gen_20250729_211033_3824e2f2.json
│       │   │   ├── lsi_gen_20250730_092840_7ea328e1.json
│       │   │   ├── lsi_gen_20250730_161453_8ae85fab.json
│       │   │   └── lsi_generation.log
│       │   └── xynapse_traces_batch_LSI.csv
│       ├── metadata
│       │   ├── latest_llm_completions.json
│       │   ├── latest_llm_completions_.json
│       │   ├── llm_completions__20250729_204407.json
│       │   ├── llm_completions__20250729_205607.json
│       │   ├── llm_completions__20250729_211033.json
│       │   ├── llm_completions__20250730_092840.json
│       │   ├── llm_completions__20250730_161453.json
│       │   └── llm_completions__20250801_220428.json
│       ├── processed_json
│       │   ├── AI-Driven_Science_Speed_versus_Safety.json
│       │   ├── AI-Driven_Science_Speed_versus_Safety_lsi_metadata.json
│       │   ├── Global_Renewables_Scale_versus_Scarcity.json
│       │   └── Global_Renewables_Scale_versus_Scarcity_lsi_metadata.json
│       └── raw_json_responses
│           ├── AI-Driven_Science_Speed_versus_Safety_back_cover_text.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_bibliographic_key_phrases.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_bibliography_prompt.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_custom_transcription_note_prompt.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_enhanced_mnemonics_prompt.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_foreword_prompt.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_imprint_quotes_prompt.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_en_metadata.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_en_motivation.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_ko_metadata.txt
│           ├── AI-Driven_Science_Speed_versus_Safety_storefront_get_ko_motivation.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_back_cover_text.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_bibliographic_key_phrases.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_bibliography_prompt.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_enhanced_mnemonics_prompt.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_foreword_prompt.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_imprint_quotes_prompt.txt
│           ├── Global_Renewables_Scale_versus_Scarcity_storefront_get_en_metadata.txt
│           └── Global_Renewables_Scale_versus_Scarcity_storefront_get_en_motivation.txt
├── package_project.py
├── prompt_prep_output.txt
├── prompts
│   ├── codexes_user_prompts.json
│   ├── enhanced_lsi_field_completion_prompts.json
│   ├── lsi_field_completion_prompts.json
│   ├── nimble_proprietary_prompts.json
│   └── prompts.json
├── pyproject.toml
├── requirements.txt
├── requirements_ui.txt
├── resources
│   ├── Book1.xlsx
│   ├── LSI_title_info.mov
│   ├── characters

│   ├── checkreqts.txt
│   ├── data_tables
│   │   ├── LSI
│   │   │   ├── SpineWidthLookup.xlsx
│   │   │   └── lsi_valid_contributor_codes.csv
│   │   ├── Managing ISBNs
│   │   │   ├── ISBNs_available.xlsx
│   │   │   ├── LSIdf.xlsx
│   │   │   ├── bowker.xlsx
│   │   │   └── not_in_LSI.xlsx
│   │   ├── bowker

│   │   └── kindle_quotes
│   │       └── Pratchett_bio.xlsx
│   ├── docx
│   │   ├── AI_Board_Badge.dotx
│   │   ├── AI_Board_Specs.docx
│   │   ├── AI_Board_Specs.dotx
│   │   ├── FrontMatter.dotx
│   │   ├── Word dictionary files
│   │   │   └── naval.dic
│   │   └── backmatter.dotx
│   ├── ideas
│   │   └── bet.txt
│   ├── images
│   │   ├── AILAB.jpg
│   │   ├── AILAB2.jpg
│   │   ├── Hawkeye-Pym-Arrow-Ant-Man.jpg
│   │   ├── Pages from Pillars_of_Russias_Disinformation_and_Propaganda_Ecosystem_08-04-20_1_.jpg
│   │   ├── Screenshot 2025-05-10 at 3.04.33 AM.png
│   │   ├── Screenshot 2025-05-10 at 3.06.21 AM.png
│   │   ├── Screenshot 2025-05-10 at 3.14.28 AM.png
│   │   ├── Trifecta.jpg
│   │   ├── Untitled.jpg
│   │   ├── ai_speed_v_safety.jpg
│   │   ├── chris-lawton-zvKx6ixUhWQ-unsplash.jpg
│   │   ├── dotgrid.png
│   │   ├── ed-robertson-eeSdJfLfx1A-unsplash.jpg
│   │   ├── febhaircut.jpg
│   │   ├── franki-chamaki-z4H9MYmWIMA-unsplash.jpg
│   │   ├── generate_dot_grid_image.pdf
│   │   ├── generate_dot_grid_image.png
│   │   ├── henry-be-lc7xcWebECc-unsplash.jpg
│   │   ├── jackson-so-TQ3SgrW9lkM-unsplash.jpg
│   │   ├── laura-kapfer-hmCMUZKLxa4-unsplash.jpg
│   │   ├── markus-winkler-tGBXiHcPKrM-unsplash.jpg
│   │   ├── mauro-sbicego-4hfpVsi-gSg-unsplash.jpg
│   │   ├── max-langelott-wWQ760meyWI-unsplash.jpg
│   │   ├── oldwoman.png
│   │   ├── psh.png
│   │   ├── seoul.png
│   │   ├── sunghoon.png
│   │   ├── text_hip_1_img.png
│   │   ├── text_hip_2_img.png
│   │   ├── thumbnail.jpg
│   │   └── video.png
│   ├── json
│   │   ├── BIP_truth_master_LSI_KDP_test.xlsx
│   │   ├── Goodreads
│   │   │   └── README
│   │   ├── create_book_metadata_json.py
│   │   ├── default.config
│   │   ├── gemini_prompts

│   │   ├── kdp_metadata.fields.py
│   │   ├── model_params.json
│   │   ├── test
│   │   ├── transcription-book-schedule.json
│   │   ├── xynapseSep2025.json
│   │   └── xynapse_trace_schedule.json
│   ├── markdown
│   │   └── documentation.py
│   ├── nft_assets
│   │   ├── 9781608881819_txt_v6-page015.jpeg
│   │   ├── Document-4-page001.jpeg
│   │   ├── Document-4-page002.jpeg
│   │   ├── Musashi-page042.jpeg
│   │   ├── NFTdesign-page001.jpeg
│   │   └── pxtlcountstransp-page001.jpeg
│   ├── products
│   │   └── xynapse_traces
│   │       └── July_2025
│   │           ├── AI-Driven_Science_Speed_versus_Safety_compiled.pdf
│   │           └── covers
│   │               ├── AI-Driven_Science_Speed_versus_Safety.png
│   │               ├── AI-Driven_Science_Speed_versus_Safety_thumb.png
│   │               ├── Martian_Self-Reliance_Isolation_versus_Earth_Support.png
│   │               ├── Martian_Self-Reliance_Isolation_versus_Earth_Support_thumb.png
│   │               ├── Mind-Machine_Fusion_Liberation_versus_Dependency.png
│   │               ├── Mind-Machine_Fusion_Liberation_versus_Dependency_thumb.png
│   │               ├── Visionary_Drive_Passion_versus_Peril.png
│   │               └── Visionary_Drive_Passion_versus_Peril_thumb.png
│   ├── reader_panels
│   │   └── ReaderPanels.py
│   ├── requirements.txt
│   ├── scribus
│   │   ├── Poker Size Card & Tuck Box Template.sla
│   │   ├── glossaries.sla
│   │   └── interior template.sla
│   ├── sources_of_truth
│   │   ├── BISG
│   │   │   ├── example_BISACs.txt
│   │   │   └── example_descriptions.txt
│   │   └── payments2authors
│   │       ├── Download (1).CSV
│   │       └── payments_lifetime.csv
│   ├── trimsizematrix.xlsx
│   └── yaml
│       ├── config.yaml
│       └── config.yaml.example
├── rewrite_imprint_mnemonics_prompt.py
├── rewrite_mnemonics_prompt.py
├── run_book_pipeline.py
├── sample_book.json
├── sample_schedule.json
├── sample_schedule_with_series.json
├── schedule1.csv
├── schedule2.json
├── scripts
│   ├── debug
│   │   └── debug_mnemonics.py
│   ├── debug_llm_response.py
│   ├── debug_lsi_fields.py
│   ├── debug_prompt_format.py
│   ├── debug_prompt_manager.py
│   ├── final_streamlit_test.py
│   ├── fix_corruption_advanced.py
│   ├── fix_corruption_complete.py
│   ├── fix_empty_llm_responses.py
│   ├── fix_formatting.py
│   ├── fix_formatting_comprehensive.py
│   ├── fix_llm_completions.py
│   ├── fix_llm_get_book_data.py
│   ├── fix_llm_get_book_data_for_messages.py
│   ├── fix_lsi_issues.py
│   ├── fix_mnemonics_prompt.py
│   ├── fix_mnemonics_prompt_escaping.py
│   ├── fix_mnemonics_prompt_format.py
│   ├── fix_pricing_mappings.py
│   ├── fix_remaining_lsi_issues.py
│   ├── fix_series_name.py
│   ├── fix_tranche_field_overrides.py
│   ├── import_bowker_isbns.py
│   ├── import_corrected_bowker.py
│   ├── lsi_config_debug.py
│   ├── migrate_metadata.py
│   ├── nuclear_fix.py
│   ├── optimize_logging_performance.py
│   ├── profile_logging_performance.py
│   ├── run_approval_tests.sh
│   ├── run_pipeline.sh
│   ├── validate_critical_message_filtering.py
│   ├── validate_lsi_csv.py
│   └── validate_lsi_metadata.py
├── services
│   └── codexes-factory.service
├── src
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-312.pyc
│   │   ├── genpw.cpython-312.pyc
│   │   └── pilsa_prepress.cpython-312.pyc
│   ├── codexes
│   │   ├── Codexes.py
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── Codexes.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── cli.cpython-312.pyc
│   │   │   ├── codexes-factory-home-ui.cpython-312.pyc
│   │   │   └── imprint.cpython-312.pyc
│   │   ├── cli.py
│   │   ├── codexes-factory-home-ui.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   ├── auth.cpython-312.pyc
│   │   │   │   ├── cleanup_report_generator.cpython-312.pyc
│   │   │   │   ├── config.cpython-312.pyc
│   │   │   │   ├── configuration_reference_updater.cpython-312.pyc
│   │   │   │   ├── configuration_unifier.cpython-312.pyc
│   │   │   │   ├── documentation_consolidator.cpython-312.pyc
│   │   │   │   ├── enhanced_llm_caller.cpython-312.pyc
│   │   │   │   ├── file_analysis_engine.cpython-312.pyc
│   │   │   │   ├── file_handler.cpython-312.pyc
│   │   │   │   ├── file_inventory_system.cpython-312.pyc
│   │   │   │   ├── llm_caller.cpython-312.pyc
│   │   │   │   ├── logging_config.cpython-312.pyc
│   │   │   │   ├── logging_filters.cpython-312.pyc
│   │   │   │   ├── prompt_manager.cpython-312.pyc
│   │   │   │   ├── resource_organizer.cpython-312.pyc
│   │   │   │   ├── safety_validator.cpython-312.pyc
│   │   │   │   ├── simple_auth.cpython-312.pyc
│   │   │   │   ├── statistics_reporter.cpython-312.pyc
│   │   │   │   ├── temporary_file_cleaner.cpython-312.pyc
│   │   │   │   ├── test_script_organizer.cpython-312-pytest-8.4.1.pyc
│   │   │   │   ├── test_script_organizer.cpython-312.pyc
│   │   │   │   ├── token_usage_tracker.cpython-312.pyc
│   │   │   │   ├── translations.cpython-312.pyc
│   │   │   │   ├── ui.cpython-312.pyc
│   │   │   │   ├── unified_configuration_system.cpython-312.pyc
│   │   │   │   └── utils.cpython-312.pyc
│   │   │   ├── auth.py
│   │   │   ├── cleanup_report_generator.py
│   │   │   ├── config.py
│   │   │   ├── configuration_reference_updater.py
│   │   │   ├── configuration_unifier.py
│   │   │   ├── documentation_consolidator.py
│   │   │   ├── enhanced_llm_caller.py
│   │   │   ├── file_analysis_engine.py
│   │   │   ├── file_handler.py
│   │   │   ├── file_inventory_system.py
│   │   │   ├── llm_caller.py
│   │   │   ├── logging_config.py
│   │   │   ├── logging_filters.py
│   │   │   ├── prompt_manager.py
│   │   │   ├── resource_organizer.py
│   │   │   ├── safety_validator.py
│   │   │   ├── simple_auth.py
│   │   │   ├── statistics_reporter.py
│   │   │   ├── temporary_file_cleaner.py
│   │   │   ├── test_script_organizer.py
│   │   │   ├── token_usage_tracker.py
│   │   │   ├── translations.py
│   │   │   ├── ui.py
│   │   │   ├── unified_configuration_system.py
│   │   │   └── utils.py
│   │   ├── imprint.py
│   │   ├── modules
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   └── __init__.cpython-312.pyc
│   │   │   ├── builders
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   └── llm_get_book_data.cpython-312.pyc
│   │   │   │   ├── llm_get_book_data.py
│   │   │   │   └── publishers_note_generator.py
│   │   │   ├── covers
│   │   │   │   ├── __pycache__
│   │   │   │   │   └── cover_generator.cpython-312.pyc
│   │   │   │   ├── cover_generator.py
│   │   │   │   ├── debug_scribus_args.py
│   │   │   │   ├── init.py
│   │   │   │   └── metadata2lsicoverspecs.py
│   │   │   ├── distribution
│   │   │   │   ├── ACS-codes-and-descriptions.csv
│   │   │   │   ├── LSI_ACS_header.csv
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   ├── accurate_reporting_system.cpython-312.pyc
│   │   │   │   │   ├── base_generator.cpython-312.pyc
│   │   │   │   │   ├── batch_processing_reporter.cpython-312.pyc
│   │   │   │   │   ├── bisac_category_generator.cpython-312.pyc
│   │   │   │   │   ├── bisac_field_mapping.cpython-312.pyc
│   │   │   │   │   ├── bisac_utils.cpython-312.pyc
│   │   │   │   │   ├── bisac_validator.cpython-312.pyc
│   │   │   │   │   ├── computed_field_strategies.cpython-312.pyc
│   │   │   │   │   ├── config_debugger.cpython-312.pyc
│   │   │   │   │   ├── contributor_role_mapping.cpython-312.pyc
│   │   │   │   │   ├── contributor_role_validator.cpython-312.pyc
│   │   │   │   │   ├── currency_formatter.cpython-312.pyc
│   │   │   │   │   ├── date_utils.cpython-312.pyc
│   │   │   │   │   ├── enhanced_bisac_strategy.cpython-312.pyc
│   │   │   │   │   ├── enhanced_error_handler.cpython-312.pyc
│   │   │   │   │   ├── enhanced_field_mappings.cpython-312.pyc
│   │   │   │   │   ├── enhanced_file_path_strategies.cpython-312.pyc
│   │   │   │   │   ├── enhanced_llm_completion_strategy.cpython-312.pyc
│   │   │   │   │   ├── enhanced_llm_field_completer.cpython-312.pyc
│   │   │   │   │   ├── enhanced_logging_simple.cpython-312.pyc
│   │   │   │   │   ├── error_recovery_manager.cpython-312.pyc
│   │   │   │   │   ├── field_corrections_validator.cpython-312.pyc
│   │   │   │   │   ├── field_mapping.cpython-312.pyc
│   │   │   │   │   ├── field_mapping_registry.cpython-312.pyc
│   │   │   │   │   ├── generate_catalog.cpython-312.pyc
│   │   │   │   │   ├── generation_result.cpython-312.pyc
│   │   │   │   │   ├── global_config_validator.cpython-312.pyc
│   │   │   │   │   ├── imprint_config_loader.cpython-312.pyc
│   │   │   │   │   ├── isbn_assignment.cpython-312.pyc
│   │   │   │   │   ├── isbn_database.cpython-312.pyc
│   │   │   │   │   ├── isbn_integration.cpython-312.pyc
│   │   │   │   │   ├── isbn_lookup.cpython-312.pyc
│   │   │   │   │   ├── isbn_lookup_cache.cpython-312.pyc
│   │   │   │   │   ├── isbn_scheduler.cpython-312.pyc
│   │   │   │   │   ├── json_metadata_extractor.cpython-312.pyc
│   │   │   │   │   ├── llm_field_completer.cpython-312.pyc
│   │   │   │   │   ├── lsi_acs_generator.cpython-312.pyc
│   │   │   │   │   ├── lsi_acs_generator_new.cpython-312.pyc
│   │   │   │   │   ├── lsi_configuration.cpython-312.pyc
│   │   │   │   │   ├── lsi_field_completion_integration.cpython-312.pyc
│   │   │   │   │   ├── lsi_field_completion_reporter.cpython-312.pyc
│   │   │   │   │   ├── lsi_logging_manager.cpython-312.pyc
│   │   │   │   │   ├── memory_performance_optimizer.cpython-312.pyc
│   │   │   │   │   ├── metadata_migration.cpython-312.pyc
│   │   │   │   │   ├── multi_level_config.cpython-312.pyc
│   │   │   │   │   ├── pricing_formatter.cpython-312.pyc
│   │   │   │   │   ├── pricing_strategy.cpython-312.pyc
│   │   │   │   │   ├── publisher_config_loader.cpython-312.pyc
│   │   │   │   │   ├── quote_processor.cpython-312.pyc
│   │   │   │   │   ├── robust_config_handler.cpython-312.pyc
│   │   │   │   │   ├── schedule_isbn_manager.cpython-312.pyc
│   │   │   │   │   ├── series_assigner.cpython-312.pyc
│   │   │   │   │   ├── series_description_processor.cpython-312.pyc
│   │   │   │   │   ├── series_lsi_integration.cpython-312.pyc
│   │   │   │   │   ├── series_registry.cpython-312.pyc
│   │   │   │   │   ├── short_description_mapping.cpython-312.pyc
│   │   │   │   │   ├── spine_width_calculator.cpython-312.pyc
│   │   │   │   │   ├── territorial_pricing.cpython-312.pyc
│   │   │   │   │   ├── text_formatter.cpython-312.pyc
│   │   │   │   │   ├── text_length_validator.cpython-312.pyc
│   │   │   │   │   ├── thema_subject_mapping.cpython-312.pyc
│   │   │   │   │   ├── tranche_aware_series_strategy.cpython-312.pyc
│   │   │   │   │   ├── tranche_config_debugger.cpython-312.pyc
│   │   │   │   │   ├── tranche_config_loader.cpython-312.pyc
│   │   │   │   │   ├── tranche_override_manager.cpython-312.pyc
│   │   │   │   │   ├── tranche_override_strategy.cpython-312.pyc
│   │   │   │   │   ├── tranche_override_wrapper.cpython-312.pyc
│   │   │   │   │   └── validation_utils.cpython-312.pyc
│   │   │   │   ├── accurate_reporting_system.py
│   │   │   │   ├── annotation_processor.py
│   │   │   │   ├── base_generator.py
│   │   │   │   ├── batch_processing_reporter.py
│   │   │   │   ├── bisac_category_analyzer.py
│   │   │   │   ├── bisac_category_generator.py
│   │   │   │   ├── bisac_field_mapping.py
│   │   │   │   ├── bisac_utils.py
│   │   │   │   ├── bisac_validator.py
│   │   │   │   ├── computed_field_strategies.py
│   │   │   │   ├── config_debugger.py
│   │   │   │   ├── config_loader_base.py
│   │   │   │   ├── contributor_role_fixer.py
│   │   │   │   ├── contributor_role_mapping.py
│   │   │   │   ├── contributor_role_validator.py
│   │   │   │   ├── currency_formatter.py
│   │   │   │   ├── date_utils.py
│   │   │   │   ├── empty_response_handler.py
│   │   │   │   ├── enhanced_bisac_strategy.py
│   │   │   │   ├── enhanced_error_handler.py
│   │   │   │   ├── enhanced_field_mappings.py
│   │   │   │   ├── enhanced_file_path_strategies.py
│   │   │   │   ├── enhanced_llm_completion_strategy.py
│   │   │   │   ├── enhanced_llm_field_completer.py
│   │   │   │   ├── enhanced_logging.py
│   │   │   │   ├── enhanced_logging_simple.py
│   │   │   │   ├── enhanced_pricing_strategy.py
│   │   │   │   ├── error_recovery.py
│   │   │   │   ├── error_recovery_manager.py
│   │   │   │   ├── field_corrections_validator.py
│   │   │   │   ├── field_mapping.py
│   │   │   │   ├── field_mapping_registry.py
│   │   │   │   ├── field_mapping_transformer.py
│   │   │   │   ├── file_path_generator.py
│   │   │   │   ├── fixlist
│   │   │   │   ├── fixlist.tsv.code-workspace
│   │   │   │   ├── fixlist.txt
│   │   │   │   ├── gc_market_pricing.py
│   │   │   │   ├── generate_catalog.py
│   │   │   │   ├── generation_result.py
│   │   │   │   ├── global_config_validator.py
│   │   │   │   ├── imprint_config_loader.py
│   │   │   │   ├── isbn_assignment.py
│   │   │   │   ├── isbn_barcode_generator.py
│   │   │   │   ├── isbn_database.py
│   │   │   │   ├── isbn_integration.py
│   │   │   │   ├── isbn_lookup.py
│   │   │   │   ├── isbn_lookup_cache.py
│   │   │   │   ├── isbn_scheduler.py
│   │   │   │   ├── json_metadata_extractor.py
│   │   │   │   ├── llm_field_completer.py
│   │   │   │   ├── llm_field_completer_fixed.py
│   │   │   │   ├── lsi_acs_generator.py
│   │   │   │   ├── lsi_acs_generator.py.bak
│   │   │   │   ├── lsi_acs_generator_new.py
│   │   │   │   ├── lsi_acs_spreadsheet_generator.py
│   │   │   │   ├── lsi_configuration.py
│   │   │   │   ├── lsi_field_completion_integration.py
│   │   │   │   ├── lsi_field_completion_reporter.py
│   │   │   │   ├── lsi_field_validator.py
│   │   │   │   ├── lsi_logging_manager.py
│   │   │   │   ├── lsi_valid_contributor_codes.csv
│   │   │   │   ├── lsi_valid_contributor_codes.csv.xlsx
│   │   │   │   ├── lsi_valid_rendition_booktypes.txt
│   │   │   │   ├── memory_performance_optimizer.py
│   │   │   │   ├── metadata_migration.py
│   │   │   │   ├── multi_level_config.py
│   │   │   │   ├── pricing_formatter.py
│   │   │   │   ├── pricing_strategy.py
│   │   │   │   ├── pricing_validator.py
│   │   │   │   ├── publisher_config_loader.py
│   │   │   │   ├── quote_assembly_optimizer.py
│   │   │   │   ├── quote_processor.py
│   │   │   │   ├── rebuild_catalog.py
│   │   │   │   ├── reserved_fields_manager.py
│   │   │   │   ├── robust_config_handler.py
│   │   │   │   ├── schedule_isbn_manager.py
│   │   │   │   ├── series_assigner.py
│   │   │   │   ├── series_cli.py
│   │   │   │   ├── series_description_processor.py
│   │   │   │   ├── series_lsi_integration.py
│   │   │   │   ├── series_pipeline_integration.py
│   │   │   │   ├── series_registry.py
│   │   │   │   ├── series_ui_integration.py
│   │   │   │   ├── short_description_mapping.py
│   │   │   │   ├── spine_width_calculator.py
│   │   │   │   ├── storefront_generator.py
│   │   │   │   ├── storefront_metadata_manager.py
│   │   │   │   ├── territorial_pricing.py
│   │   │   │   ├── text_formatter.py
│   │   │   │   ├── text_length_validator.py
│   │   │   │   ├── thema_subject_mapping.py
│   │   │   │   ├── tranche_aware_series_strategy.py
│   │   │   │   ├── tranche_config_debugger.py
│   │   │   │   ├── tranche_config_loader.py
│   │   │   │   ├── tranche_override_manager.py
│   │   │   │   ├── tranche_override_strategy.py
│   │   │   │   ├── tranche_override_wrapper.py
│   │   │   │   ├── validation_reporter.py
│   │   │   │   ├── validation_utils.py
│   │   │   │   └── writing_style_manager.py
│   │   │   ├── editing
│   │   │   │   └── sensitivity
│   │   │   │       ├── __init__.py
│   │   │   │       └── sensitivity_standards.py
│   │   │   ├── finance

│   │   │   ├── ideation
│   │   │   │   ├── analytics
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── pattern_analyzer.py
│   │   │   │   ├── batch
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── automation_engine.py
│   │   │   │   │   ├── batch_processor.py
│   │   │   │   │   └── progress_tracker.py
│   │   │   │   ├── collaboration
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── session_manager.py
│   │   │   │   ├── continuous
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── auto_tournament.py
│   │   │   │   │   ├── continuous_generator.py
│   │   │   │   │   └── generation_monitor.py
│   │   │   │   ├── core
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __pycache__
│   │   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   │   ├── classification.cpython-312.pyc
│   │   │   │   │   │   ├── codex_object.cpython-312.pyc
│   │   │   │   │   │   └── transformation.cpython-312.pyc
│   │   │   │   │   ├── classification.py
│   │   │   │   │   ├── codex_object.py
│   │   │   │   │   └── transformation.py
│   │   │   │   ├── elements
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── element_categorizer.py
│   │   │   │   │   ├── element_extractor.py
│   │   │   │   │   ├── element_selector.py
│   │   │   │   │   └── recombination_engine.py
│   │   │   │   ├── error_handling
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── integration
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── llm
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __pycache__
│   │   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   │   ├── ideation_llm_service.cpython-312.pyc
│   │   │   │   │   │   ├── prompt_manager.cpython-312.pyc
│   │   │   │   │   │   └── response_parser.cpython-312.pyc
│   │   │   │   │   ├── ideation_llm_service.py
│   │   │   │   │   ├── prompt_manager.py
│   │   │   │   │   └── response_parser.py
│   │   │   │   ├── longform
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── migration
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── performance
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── __pycache__
│   │   │   │   │       └── __init__.cpython-312.pyc
│   │   │   │   ├── prompts
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── series
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __pycache__
│   │   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   │   ├── consistency_manager.cpython-312.pyc
│   │   │   │   │   │   ├── franchise_manager.cpython-312.pyc
│   │   │   │   │   │   └── series_generator.cpython-312.pyc
│   │   │   │   │   ├── consistency_manager.py
│   │   │   │   │   ├── franchise_manager.py
│   │   │   │   │   ├── franchise_manager_minimal.py
│   │   │   │   │   └── series_generator.py
│   │   │   │   ├── storage
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __pycache__
│   │   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   │   ├── database_manager.cpython-312.pyc
│   │   │   │   │   │   ├── file_manager.cpython-312.pyc
│   │   │   │   │   │   └── migrations.cpython-312.pyc
│   │   │   │   │   ├── database_manager.py
│   │   │   │   │   ├── file_manager.py
│   │   │   │   │   └── migrations.py
│   │   │   │   ├── synthetic_readers
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __pycache__
│   │   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   │   ├── evaluation_aggregator.cpython-312.pyc
│   │   │   │   │   │   ├── reader_panel.cpython-312.pyc
│   │   │   │   │   │   └── reader_persona.cpython-312.pyc
│   │   │   │   │   ├── evaluation_aggregator.py
│   │   │   │   │   ├── reader_panel.py
│   │   │   │   │   └── reader_persona.py
│   │   │   │   ├── tournament
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── __pycache__
│   │   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   │   ├── bracket_generator.cpython-312.pyc
│   │   │   │   │   │   ├── evaluation_engine.cpython-312.pyc
│   │   │   │   │   │   ├── results_manager.cpython-312.pyc
│   │   │   │   │   │   └── tournament_engine.cpython-312.pyc
│   │   │   │   │   ├── bracket_generator.py
│   │   │   │   │   ├── evaluation_engine.py
│   │   │   │   │   ├── results_manager.py
│   │   │   │   │   └── tournament_engine.py
│   │   │   │   └── ui
│   │   │   │       ├── __init__.py
│   │   │   │       ├── __pycache__
│   │   │   │       │   └── __init__.cpython-312.pyc
│   │   │   │       ├── components
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── __pycache__
│   │   │   │       │   │   ├── __init__.cpython-312.pyc
│   │   │   │       │   │   └── universal_input.cpython-312.pyc
│   │   │   │       │   └── universal_input.py
│   │   │   │       ├── config
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── __pycache__
│   │   │   │       │   │   ├── __init__.cpython-312.pyc
│   │   │   │       │   │   └── model_config.cpython-312.pyc
│   │   │   │       │   ├── default_models.json
│   │   │   │       │   └── model_config.py
│   │   │   │       └── core
│   │   │   │           ├── __init__.py
│   │   │   │           ├── __pycache__
│   │   │   │           │   ├── __init__.cpython-312.pyc
│   │   │   │           │   └── simple_codex_object.cpython-312.pyc
│   │   │   │           └── simple_codex_object.py
│   │   │   ├── metadata
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   ├── metadata_generator.cpython-312.pyc
│   │   │   │   │   └── metadata_models.cpython-312.pyc
│   │   │   │   ├── metadata_generator.py
│   │   │   │   ├── metadata_models.py
│   │   │   │   └── series-prototypes
│   │   │   │       ├── BookSeries
│   │   │   │       │   ├── CreateSeries.py
│   │   │   │       │   ├── ImagePromptGenerator.json
│   │   │   │       │   ├── __init__.py
│   │   │   │       │   ├── createbookdocxbyrows.py
│   │   │   │       │   ├── createbookoutline.py
│   │   │   │       │   ├── createdocxbyrows.py
│   │   │   │       │   ├── daddysphone.txt
│   │   │   │       │   └── text2midjourney_diffusion.py
│   │   │   │       ├── CreateSeries.py
│   │   │   │       └── Create_Book_Series
│   │   │   ├── prepress
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   ├── bibliography_formatter.cpython-312.pyc
│   │   │   │   │   ├── glossary_layout_manager.cpython-312.pyc
│   │   │   │   │   ├── partsofthebook_processor.cpython-312.pyc
│   │   │   │   │   ├── tex_utils.cpython-312.pyc
│   │   │   │   │   └── typography_manager.cpython-312.pyc
│   │   │   │   ├── bibliography_formatter.py
│   │   │   │   ├── generate_dot_grid.py
│   │   │   │   ├── glossary_layout_manager.py
│   │   │   │   ├── last_verso_page_manager.py
│   │   │   │   ├── mnemonics_json_processor.py
│   │   │   │   ├── new.sh
│   │   │   │   ├── partsofthebook_processor.py
│   │   │   │   ├── pilsa_book_content_processor.py
│   │   │   │   ├── publishers_note_generator.py
│   │   │   │   ├── quote_assembly_optimizer.py
│   │   │   │   ├── tex_utils.py
│   │   │   │   ├── typography_manager.py
│   │   │   │   └── writing_style_manager.py
│   │   │   ├── social

│   │   │   ├── ui
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   ├── command_builder.cpython-312.pyc
│   │   │   │   │   ├── config_synchronizer.cpython-312.pyc
│   │   │   │   │   ├── config_validator.cpython-312.pyc
│   │   │   │   │   ├── configuration_manager.cpython-312.pyc
│   │   │   │   │   ├── dropdown_manager.cpython-312.pyc
│   │   │   │   │   ├── dynamic_config_loader.cpython-312.pyc
│   │   │   │   │   ├── parameter_groups.cpython-312.pyc
│   │   │   │   │   ├── state_manager.cpython-312.pyc
│   │   │   │   │   ├── streamlit_components.cpython-312.pyc
│   │   │   │   │   ├── tranche_config_ui_manager.cpython-312.pyc
│   │   │   │   │   └── validation_manager.cpython-312.pyc
│   │   │   │   ├── command_builder.py
│   │   │   │   ├── config_aware_validator.py
│   │   │   │   ├── config_synchronizer.py
│   │   │   │   ├── config_validator.py
│   │   │   │   ├── configuration_manager.py
│   │   │   │   ├── dropdown_manager.py
│   │   │   │   ├── dynamic_config_loader.py
│   │   │   │   ├── parameter_groups.py
│   │   │   │   ├── state_manager.py
│   │   │   │   ├── streamlit_components.py
│   │   │   │   ├── tranche_config_ui_manager.py
│   │   │   │   └── validation_manager.py
│   │   │   └── verifiers
│   │   │       ├── __pycache__
│   │   │       │   ├── field_validators.cpython-312.pyc
│   │   │       │   ├── quote_verifier.cpython-312.pyc
│   │   │       │   └── validation_framework.cpython-312.pyc
│   │   │       ├── field_validators.py
│   │   │       ├── ignore.txt
│   │   │       ├── quote_verifier.py
│   │   │       └── validation_framework.py
│   │   ├── pages
│   │   │   ├── 10_Book_Pipeline.py
│   │   │   ├── 11_Backmatter_Manager.py
│   │   │   ├── 12_Bibliography_Shopping.py
│   │   │   ├── 12_Schedule_ISBN_Manager.py
│   │   │   ├── 13_ISBN_Schedule_Manager.py
│   │   │   ├── 14_ISBN_Management.py
│   │   │   ├── 16_Stage_Agnostic_UI.py
│   │   │   ├── 1_Home.py
│   │   │   ├── 2_Ideation_and_Development.py
│   │   │   ├── 3_Manuscript_Enhancement.py
│   │   │   ├── 4_Metadata_and_Distribution.py
│   │   │   ├── 5_Settings_and_Commerce.py
│   │   │   ├── 6_Bookstore.py
│   │   │   ├── 7_Admin_Dashboard.py
│   │   │   ├── 8_Login_Register.py
│   │   │   ├── 9_Imprint_Builder.py
│   │   │   ├── Configuration_Management.py
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   └── __init__.cpython-312.pyc
│   │   │   ├── ideation_dashboard.py
│   │   │   └── tournament_interface.py
│   │   ├── ui
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   └── __init__.cpython-312.pyc
│   │   │   ├── adapters
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   └── workflow_adapter.cpython-312.pyc
│   │   │   │   └── workflow_adapter.py
│   │   │   ├── components
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   ├── adaptive_form.cpython-312.pyc
│   │   │   │   │   ├── content_detector.cpython-312.pyc
│   │   │   │   │   ├── content_filter.cpython-312.pyc
│   │   │   │   │   ├── file_handler.cpython-312.pyc
│   │   │   │   │   ├── imprint_ideation_bridge.cpython-312.pyc
│   │   │   │   │   ├── object_datatable.cpython-312.pyc
│   │   │   │   │   ├── transformation_interface.cpython-312.pyc
│   │   │   │   │   ├── universal_input.cpython-312.pyc
│   │   │   │   │   ├── workflow_analytics.cpython-312.pyc
│   │   │   │   │   ├── workflow_automation.cpython-312.pyc
│   │   │   │   │   ├── workflow_export.cpython-312.pyc
│   │   │   │   │   ├── workflow_selector.cpython-312.pyc
│   │   │   │   │   └── workflow_templates.cpython-312.pyc
│   │   │   │   ├── adaptive_form.py
│   │   │   │   ├── content_detector.py
│   │   │   │   ├── content_filter.py
│   │   │   │   ├── file_handler.py
│   │   │   │   ├── imprint_ideation_bridge.py
│   │   │   │   ├── mixed_type_evaluator.py
│   │   │   │   ├── object_datatable.py
│   │   │   │   ├── transformation_interface.py
│   │   │   │   ├── universal_input.py
│   │   │   │   ├── workflow_analytics.py
│   │   │   │   ├── workflow_automation.py
│   │   │   │   ├── workflow_export.py
│   │   │   │   ├── workflow_selector.py
│   │   │   │   └── workflow_templates.py
│   │   │   ├── config
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   └── model_config.cpython-312.pyc
│   │   │   │   ├── default_models.json
│   │   │   │   └── model_config.py
│   │   │   ├── core
│   │   │   │   ├── __init__.py
│   │   │   │   ├── __pycache__
│   │   │   │   │   ├── __init__.cpython-312.pyc
│   │   │   │   │   └── simple_codex_object.cpython-312.pyc
│   │   │   │   └── simple_codex_object.py
│   │   │   └── field_configs
│   │   │       ├── __init__.py
│   │   │       ├── __pycache__
│   │   │       │   ├── __init__.cpython-312.pyc
│   │   │       │   ├── draft_fields.cpython-312.pyc
│   │   │       │   ├── idea_fields.cpython-312.pyc
│   │   │       │   ├── outline_fields.cpython-312.pyc
│   │   │       │   ├── synopsis_fields.cpython-312.pyc
│   │   │       │   └── universal_fields.cpython-312.pyc
│   │   │       ├── draft_fields.py
│   │   │       ├── idea_fields.py
│   │   │       ├── outline_fields.py
│   │   │       ├── synopsis_fields.py
│   │   │       └── universal_fields.py
│   │   └── utilities
│   │       └── prompt_modernizer.py
│   ├── codexes_factory.egg-info
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   ├── dependency_links.txt
│   │   ├── requires.txt
│   │   └── top_level.txt
│   ├── genpw.py
│   └── pilsa_prepress.py
├── start_streamlit.py
├── start_streamlit.sh
├── streamlit_servers.json
├── system_integrity_validation_20250826_231553.json
├── system_integrity_validation_20250826_231916.json
├── system_integrity_validation_20250826_231949.json
├── temp_model_params.json
├── templates
│   ├── BerkshireSwash-Regular.ttf
│   ├── LSI_ACS_header.csv
│   ├── codes.csv
│   ├── cover_template.tex
│   ├── dotgrid.png
│   ├── images

│   ├── lsi_full_template.csv
│   ├── lsi_template.csv
│   ├── new.sh
│   ├── new2.sh
│   ├── punch_list_by_stage
│   ├── template.tex
│   ├── template.xml
│   └── test_cover.tex
├── test_cleanup_reports
│   ├── cleanup_20250826_231817_initial_snapshot.json
│   ├── cleanup_report_20250826_231817.html
│   ├── cleanup_report_20250826_231817.json
│   ├── cleanup_report_20250826_231817.md
│   ├── directory_structure_20250826_231817.md
│   └── validation_summary_20250826_231817.md
├── test_output
│   ├── raw_json_responses
│   │   └── test_book_mnemonics_prompt.txt
│   ├── test_book.json
│   └── test_mnemonic_imprint_quotes_prompt.txt
├── test_pipeline_success_messages.py
├── tests
│   ├── __pycache__
│   │   ├── run_complete_test.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_accurate_reporting_system.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_annotation_processor.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_annotation_processor.cpython-312.pyc
│   │   ├── test_auth_and_imprint_fixes.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_autofix_compatibility.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_backmatter_improvements.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_backward_compatibility.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_basic_ui.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_batch_models.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_batch_orchestrator.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_batch_processor.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_bibliography_formatter.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_bisac_field_mapping.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_bisac_field_mapping.cpython-312.pyc
│   │   ├── test_bisac_utils.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_bisac_utils.cpython-312.pyc
│   │   ├── test_book_production_fixes.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_book_production_fixes_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_command_builder_fix.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_complete_config_system.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_complete_error_handling.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_complete_logging_flow.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_complete_ui_fix.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_comprehensive_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_computed_strategies.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_config_sync.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_configuration_reference_updater.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_configuration_unifier.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_configuration_validation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_content_detection.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_contributor_role_mapping.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_contributor_role_mapping.cpython-312.pyc
│   │   ├── test_contributor_role_validator.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_contributor_role_validator.cpython-312.pyc
│   │   ├── test_cover_fixes.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_csv_reader.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_currency_formatter.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_date_computation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_date_utils.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_date_utils.cpython-312.pyc
│   │   ├── test_direct_mnemonics.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_directory_scanner.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_documentation_consolidator.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_dropdown_fix.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_error_handler.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_error_handling.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_field_mapping_registry.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_field_mapping_registry.cpython-312.pyc
│   │   ├── test_enhanced_field_mapping_registry.cpython-313.pyc
│   │   ├── test_enhanced_field_mapping_strategies.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_field_mappings.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_field_mappings.cpython-312.pyc
│   │   ├── test_enhanced_llm_caller_compatibility.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_llm_completion_strategy.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_llm_completion_strategy.cpython-312.pyc
│   │   ├── test_enhanced_llm_completion_strategy.cpython-313.pyc
│   │   ├── test_enhanced_metadata_generation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_enhanced_metadata_generation.cpython-312.pyc
│   │   ├── test_error_handler.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_error_handling_retry_logic.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_error_recovery_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_error_recovery_manager.cpython-312.pyc
│   │   ├── test_expand_imprint_cli.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_field_corrections_validator.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_field_exclusions.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_field_exclusions.cpython-312.pyc
│   │   ├── test_field_mapping.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_field_mapping.cpython-312.pyc
│   │   ├── test_field_validators.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_field_validators.cpython-312.pyc
│   │   ├── test_field_value_extraction.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_field_value_extraction.cpython-312.pyc
│   │   ├── test_field_value_extraction.cpython-313.pyc
│   │   ├── test_file_path_generation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_file_system_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_file_system_integration.cpython-312.pyc
│   │   ├── test_full_book_pipeline.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_gc_market_pricing.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_gc_market_pricing.cpython-312.pyc
│   │   ├── test_generation_result.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_generation_result.cpython-312.pyc
│   │   ├── test_global_instance.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_glossary_layout_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_groq_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_imprint_config.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_imprint_ideation_bridge.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_instance_type.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_intelligent_fallbacks.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_interior_fixes.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_isbn_assignment.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_isbn_assignment.cpython-312.pyc
│   │   ├── test_isbn_database.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_isbn_database.cpython-312.pyc
│   │   ├── test_isbn_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_isbn_lookup_cache.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_isbn_scheduler.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_json_metadata_extractor.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_json_parsing.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_litellm_filter.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_live_pipeline.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_llm_caller_enhancements.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_llm_completions.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_llm_field_completer.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_llm_field_completer.cpython-312.pyc
│   │   ├── test_llm_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_llm_integration.cpython-312.pyc
│   │   ├── test_log_success_function.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_comprehensive.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_config.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_configuration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_error_scenarios.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_performance_optimization.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_logging_stress_scenarios.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_bug_fixes.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_configuration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_configuration.cpython-312.pyc
│   │   ├── test_lsi_field_completion_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_field_completion_integration.cpython-312.pyc
│   │   ├── test_lsi_field_completion_reporter.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_field_completion_reporter.cpython-312.pyc
│   │   ├── test_lsi_field_completion_reporter.cpython-313.pyc
│   │   ├── test_lsi_field_corrections_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_field_corrections_performance.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_field_corrections_validation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_integration.cpython-312.pyc
│   │   ├── test_lsi_logging_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_logging_manager.cpython-312.pyc
│   │   ├── test_lsi_performance.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_system_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_lsi_validation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_metadata_migration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_metadata_migration.cpython-312.pyc
│   │   ├── test_mnemonic_extraction.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_latex_escaping.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_latex_escaping.cpython-312.pyc
│   │   ├── test_mnemonic_latex_generation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_llm_call.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_llm_debug.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_prompt_preparation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonic_system_complete.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonics_direct.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_mnemonics_with_messages.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_modernized_prompts.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_multi_level_config.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_multiple_objects.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_nimble_llm_caller.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_nimble_methods.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_nimble_no_logger.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_nimble_simple.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_openai_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_output_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_pdf_file_validators.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_pdf_file_validators.cpython-312.pyc
│   │   ├── test_physical_specs.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_pilsa_formatting.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_pipeline_success_guarantee_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_pipeline_token_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_prompt_loading_substitution.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_quotes_per_book.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_real_api_integration.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_rendition_booktype_validation.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_resource_organizer.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_runaway_fixes.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_schedule_isbn_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_series_assigner.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_series_assigner.cpython-312.pyc
│   │   ├── test_series_description_processor.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_series_registry.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_series_registry.cpython-312.pyc
│   │   ├── test_short_description_mapping.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_short_description_mapping.cpython-312.pyc
│   │   ├── test_simple_tournament.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_single_mnemonic.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_statistics_reporter.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_streamlit_imports.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_streamlit_pages.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_success_message_filtering.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_success_message_guarantee_fix.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_system_integrity_validation.cpython-312.pyc
│   │   ├── test_task2_acceptance.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_task2_complete.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_temporary_file_cleaner.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_test_script_organizer.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_text_length_validator.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_text_length_validator.cpython-312.pyc
│   │   ├── test_textbf_line_detection.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_thema_subject_mapping.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_thema_subject_mapping.cpython-312.pyc
│   │   ├── test_token_usage_tracker.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tournament_fix.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tranche_bisac_override.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tranche_bisac_override.cpython-312.pyc
│   │   ├── test_tranche_config.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tranche_config_loader_updates.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tranche_config_ui_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tranche_override_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_tranche_override_wrapper.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_typography_manager.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_ui_components.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_ui_imports.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_ui_safety_patterns.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_validation_fix.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_validation_framework.cpython-312-pytest-8.4.1.pyc
│   │   ├── test_validation_framework.cpython-312.pyc
│   │   ├── test_workflow_interface_integration.cpython-312-pytest-8.4.1.pyc
│   │   └── test_xynapse_traces_pipeline.cpython-312-pytest-8.4.1.pyc
│   ├── compile_test_font.sh
│   ├── debug_class_methods.py
│   ├── direct_test_output.txt
│   ├── direct_test_output.txt.mock_llm_call.json
│   ├── integration_test_lsi_enhancement.py
│   ├── korean_font_test.pdf
│   ├── modules
│   │   └── ideation
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       │   └── __init__.cpython-312.pyc
│   │       ├── test_core
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   ├── test_classification.cpython-312-pytest-8.4.1.pyc
│   │       │   │   ├── test_codex_object.cpython-312-pytest-8.4.1.pyc
│   │       │   │   └── test_transformation.cpython-312-pytest-8.4.1.pyc
│   │       │   ├── test_classification.py
│   │       │   ├── test_codex_object.py
│   │       │   └── test_transformation.py
│   │       ├── test_integration
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   └── test_full_workflow.cpython-312-pytest-8.4.1.pyc
│   │       │   └── test_full_workflow.py
│   │       ├── test_llm
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   └── test_ideation_llm_service.cpython-312-pytest-8.4.1.pyc
│   │       │   └── test_ideation_llm_service.py
│   │       ├── test_performance
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   └── test_cache_manager.cpython-312-pytest-8.4.1.pyc
│   │       │   └── test_cache_manager.py
│   │       ├── test_storage
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   ├── test_database_manager.cpython-312-pytest-8.4.1.pyc
│   │       │   │   └── test_file_manager.cpython-312-pytest-8.4.1.pyc
│   │       │   ├── test_database_manager.py
│   │       │   └── test_file_manager.py
│   │       ├── test_tournament
│   │       │   ├── __init__.py
│   │       │   ├── __pycache__
│   │       │   │   ├── __init__.cpython-312.pyc
│   │       │   │   ├── test_results_manager.cpython-312-pytest-8.4.1.pyc
│   │       │   │   └── test_tournament_engine.cpython-312-pytest-8.4.1.pyc
│   │       │   ├── test_results_manager.py
│   │       │   └── test_tournament_engine.py
│   │       └── ui
│   │           ├── __init__.py
│   │           ├── __pycache__
│   │           │   ├── __init__.cpython-312.pyc
│   │           │   ├── test_content_detector.cpython-312-pytest-8.4.1.pyc
│   │           │   └── test_universal_input.cpython-312-pytest-8.4.1.pyc
│   │           ├── test_content_detector.py
│   │           └── test_universal_input.py
│   ├── pipeline

│   ├── run_book_pipeline_series_integration.patch
│   ├── run_book_pipeline_updated.py
│   ├── run_complete_test.py
│   ├── run_comprehensive_cleanup_validation.py
│   ├── run_direct_mnemonics.sh
│   ├── run_mnemonic_tests.sh
│   ├── run_mnemonics_debug.sh
│   ├── run_mnemonics_test.sh
│   ├── run_mnemonics_test_fixed.sh
│   ├── run_system_integrity_validation.py
│   ├── run_test_compile_log.sh
│   ├── run_test_font.sh
│   ├── test.db
│   ├── test.log
│   ├── test_accurate_reporting_system.py
│   ├── test_annotation_debug.csv
│   ├── test_annotation_fixed.csv
│   ├── test_annotation_processor.py
│   ├── test_auth_and_imprint_fixes.py
│   ├── test_backmatter_improvements.py
│   ├── test_backward_compatibility.py
│   ├── test_basic_ui.py
│   ├── test_bibliography_formatter.py
│   ├── test_bisac_field_mapping.py
│   ├── test_bisac_utils.py
│   ├── test_book_production_fixes.py
│   ├── test_book_production_fixes_integration.py
│   ├── test_cleanup_report_generator.py
│   ├── test_command_builder_fix.py
│   ├── test_complete_config_system.py
│   ├── test_complete_error_handling.py
│   ├── test_complete_logging_flow.py
│   ├── test_complete_ui_fix.py
│   ├── test_comprehensive_integration.py
│   ├── test_computed_strategies.py
│   ├── test_config_sync.py
│   ├── test_configuration_reference_updater.py
│   ├── test_configuration_unifier.py
│   ├── test_configuration_validation.py
│   ├── test_content_detection.py
│   ├── test_contributor_role_mapping.py
│   ├── test_contributor_role_validator.py
│   ├── test_cover.aux
│   ├── test_cover.pdf
│   ├── test_cover_fixes.py
│   ├── test_currency_formatter.py
│   ├── test_data
│   │   ├── example_outputs

│   │   ├── isbn_samples
│   │   │   ├── create_sample_bowker_excel.py
│   │   │   ├── sample_bowker.csv
│   │   │   ├── sample_bowker_complex.xlsx
│   │   │   └── test_bowker.csv
│   │   └── sample_metadata.py
│   ├── test_date_computation.py
│   ├── test_date_utils.py
│   ├── test_direct_mnemonics.py
│   ├── test_documentation_consolidator.py
│   ├── test_dropdown_fix.py
│   ├── test_enhanced_error_handler.py
│   ├── test_enhanced_error_handling.py
│   ├── test_enhanced_field_mapping_registry.py
│   ├── test_enhanced_field_mapping_strategies.py
│   ├── test_enhanced_field_mappings.py
│   ├── test_enhanced_llm_caller_compatibility.py
│   ├── test_enhanced_llm_completion_strategy.py
│   ├── test_enhanced_metadata_generation.py
│   ├── test_error_handling_retry_logic.py
│   ├── test_error_recovery_manager.py
│   ├── test_field_corrections_validator.py
│   ├── test_field_exclusions.py
│   ├── test_field_mapping.py
│   ├── test_field_validators.py
│   ├── test_field_value_extraction.py
│   ├── test_file_path_generation.py
│   ├── test_file_system_integration.py
│   ├── test_final_check.csv
│   ├── test_font.tex
│   ├── test_full_book_pipeline.py
│   ├── test_gc_market_pricing.py
│   ├── test_generation_result.py
│   ├── test_global_instance.py
│   ├── test_glossary_fix_schedule.json
│   ├── test_glossary_layout_manager.py
│   ├── test_groq_integration.py
│   ├── test_imprint_config.py
│   ├── test_imprint_ideation_bridge.py
│   ├── test_instance_type.py
│   ├── test_intelligent_fallbacks.py
│   ├── test_interior_fixes.py
│   ├── test_invalid.csv
│   ├── test_isbn_assignment.py
│   ├── test_isbn_database.py
│   ├── test_isbn_integration.py
│   ├── test_isbn_lookup_cache.py
│   ├── test_isbn_scheduler.py
│   ├── test_json_metadata_extractor.py
│   ├── test_json_parsing.py
│   ├── test_litellm_filter.py
│   ├── test_live_pipeline.py
│   ├── test_llm_caller_enhancements.py
│   ├── test_llm_completion.csv
│   ├── test_llm_completions.py
│   ├── test_llm_field_completer.py
│   ├── test_llm_fixed.csv
│   ├── test_llm_integration.py
│   ├── test_log_success_function.py
│   ├── test_logging_comprehensive.py
│   ├── test_logging_config.py
│   ├── test_logging_configuration.py
│   ├── test_logging_error_scenarios.py
│   ├── test_logging_integration.py
│   ├── test_logging_performance_optimization.py
│   ├── test_logging_stress_scenarios.py
│   ├── test_lsi_bug_fixes.py
│   ├── test_lsi_configuration.py
│   ├── test_lsi_enhanced.csv
│   ├── test_lsi_field_completion_integration.py
│   ├── test_lsi_field_completion_reporter.py
│   ├── test_lsi_field_corrections_integration.py
│   ├── test_lsi_field_corrections_performance.py
│   ├── test_lsi_field_corrections_validation.py
│   ├── test_lsi_full.csv
│   ├── test_lsi_integration.py
│   ├── test_lsi_logging_manager.py
│   ├── test_lsi_output.csv
│   ├── test_lsi_performance.py
│   ├── test_lsi_system_integration.py
│   ├── test_lsi_validation.py
│   ├── test_mars_book.csv
│   ├── test_metadata_migration.py
│   ├── test_mnemonic_extraction.py
│   ├── test_mnemonic_integration.py
│   ├── test_mnemonic_latex_escaping.py
│   ├── test_mnemonic_latex_generation.py
│   ├── test_mnemonic_llm_call.py
│   ├── test_mnemonic_llm_debug.py
│   ├── test_mnemonic_prompt_preparation.py
│   ├── test_mnemonic_system_complete.py
│   ├── test_mnemonics_book.json
│   ├── test_mnemonics_direct.py
│   ├── test_mnemonics_with_messages.py
│   ├── test_mnemonics_with_messages_output.json
│   ├── test_mock_quotes.json
│   ├── test_modernized_prompts.py
│   ├── test_multi_level_config.py
│   ├── test_multiple_objects.py
│   ├── test_nimble_llm_caller.py
│   ├── test_nimble_methods.py
│   ├── test_nimble_no_logger.py
│   ├── test_nimble_simple.py
│   ├── test_openai_integration.py
│   ├── test_pdf_file_validators.py
│   ├── test_physical_specs.py
│   ├── test_pilsa_formatting.py
│   ├── test_pipeline_end_to_end_logging.py
│   ├── test_pipeline_success_guarantee_integration.py
│   ├── test_pipeline_token_integration.py
│   ├── test_prompt_loading_substitution.py
│   ├── test_quotes_per_book.py
│   ├── test_real_api_integration.py
│   ├── test_rendition_booktype_validation.py
│   ├── test_resource_organizer.py
│   ├── test_runaway_fixes.py
│   ├── test_schedule.csv
│   ├── test_schedule_isbn_manager.py
│   ├── test_series_assigner.py
│   ├── test_series_description_processor.py
│   ├── test_series_fix.csv
│   ├── test_series_registry.py
│   ├── test_short_description_mapping.py
│   ├── test_simple_tournament.py
│   ├── test_single_mnemonic.py
│   ├── test_statistics_reporter.py
│   ├── test_streamlit_imports.py
│   ├── test_streamlit_pages.py
│   ├── test_success_message_filtering.py
│   ├── test_success_message_guarantee_fix.py
│   ├── test_system_integrity_validation.py
│   ├── test_task2_acceptance.py
│   ├── test_task2_complete.py
│   ├── test_template.aux
│   ├── test_template.log
│   ├── test_template.pdf
│   ├── test_template.tex
│   ├── test_temporary_file_cleaner.py
│   ├── test_test_script_organizer.py
│   ├── test_text_length_validator.py
│   ├── test_textbf_line_detection.py
│   ├── test_thema_subject_mapping.py
│   ├── test_token_usage_tracker.py
│   ├── test_tournament.db
│   ├── test_tournament_fix.py
│   ├── test_tranche_bisac_override.py
│   ├── test_tranche_config.py
│   ├── test_tranche_config_loader_updates.py
│   ├── test_tranche_config_ui_manager.py
│   ├── test_tranche_override_manager.py
│   ├── test_tranche_override_wrapper.py
│   ├── test_typography_manager.py
│   ├── test_ui_components.py
│   ├── test_ui_imports.py
│   ├── test_validation_fix.py
│   ├── test_validation_framework.py
│   ├── test_verification_protocol_loader.py
│   ├── test_workflow_interface_integration.py
│   └── test_xynapse_traces_pipeline.py
├── texput.log
├── text_hip_global
│   ├── 4q2025.csv
│   ├── preprocess_korean.csv
│   └── schedule.csv
├── tools
│   ├── __pycache__
│   │   ├── __init__.cpython-312.pyc
│   │   ├── enhanced_imprint_expander.cpython-312.pyc
│   │   └── expand_imprint_cli.cpython-312.pyc
│   ├── assign_schedule_isbns.py
│   ├── ingest_isbn.py
│   ├── isbn_schedule_cli.py
│   ├── report_isbns.py
│   └── schedule_converter.py
├── transform_content.py
├── transformation_history.json
├── transformation_snapshots
│   └── snapshot_20250822_015416_de945091.json
├── update_llm_get_book_data.py
├── users.json
├── uv.lock
├── validate_resource_organization.py
├── verify_password.py
└── xtuff_collections.db
```

## Directory Descriptions

- **src/** - Source code directory containing the main application code
- **src/codexes/** - Main application package
- **src/codexes/core/** - Core functionality and utilities
- **src/codexes/modules/** - Feature modules organized by functionality
- **tests/** - Test suite including unit and integration tests
- **docs/** - Documentation including guides, API docs, and summaries
- **configs/** - Configuration files for different environments and components
- **data/** - Data files including catalogs and processed content
- **logs/** - Log files from application execution
- **prompts/** - LLM prompt templates and configurations
- **resources/** - Static resources including images and templates
- **templates/** - Template files for document generation
- **examples/** - Example scripts and usage demonstrations
- **imprints/** - Imprint-specific configurations and templates
- **output/** - Generated output files and build artifacts

## File Organization Principles

The repository follows these organization principles:

1. **Source Code Separation** - All source code is in `src/`
2. **Test Isolation** - All tests are in `tests/`
3. **Documentation Centralization** - All docs are in `docs/`
4. **Configuration Hierarchy** - Configs follow inheritance patterns
5. **Resource Organization** - Static resources are properly categorized
6. **Clean Root Directory** - Minimal files in the root directory
