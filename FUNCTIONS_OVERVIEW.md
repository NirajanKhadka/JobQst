# Functions Overview

This document lists all unique function names in the codebase, grouped by file. Use this as a reference to identify redundancies and overlaps for future refactoring.

---

## src/core/utils.py
- get_utils
- save_jobs_to_json
- load_jobs_from_json
- save_jobs_to_csv
- extract_company_from_url
- normalize_location
- generate_job_hash
- is_duplicate_job
- sort_jobs
- get_job_stats
- get_available_profiles
- load_profile
- hash_job
- convert_doc_to_pdf
- save_document_as_pdf
- create_temp_file
- get_browser_user_data_dir
- check_pause_signal
- set_pause_signal
- ensure_profile_files
- save_customized_document

## src/core/user_profile_manager.py
- get_profile_manager
- get_user_profile_manager

## src/core/text_utils.py
- clean_text
- extract_keywords
- analyze_text
- normalize_job_title
- extract_skills_from_text
- format_text_for_display
- extract_contact_info

## src/core/system_utils.py
- signal_handler
- force_quit_handler
- setup_signal_handlers
- fix_ssl_cert_issue
- get_system_performance_info
- auto_start_dashboard
- is_senior_job
- validate_profile_completeness
- prompt_continue
- select_ats

## src/core/session.py
- create_session_manager
- create_rate_limiter
- create_browser_session

## src/core/ollama_manager.py
- check_ollama_installation
- install_ollama_guide
- check_ollama_service
- start_ollama_service
- check_mistral_model
- download_mistral_model
- check_ollama_status
- setup_ollama_if_needed

## src/core/job_filters.py
- create_filter_from_profile
- filter_jobs_by_priority
- filter_duplicate_jobs

## src/core/job_database.py
- get_job_db
- close_job_db

## src/core/db_engine.py
- create_database_engine

## src/core/browser_utils.py
- create_browser_utils
- create_tab_manager
- create_popup_handler

## src/core/app_runner.py
- load_profile
- show_profile_info
- run_interactive_mode
- run_scraping_mode
- run_application_mode
- run_dashboard_mode
- run_status_mode
- run_setup_mode
- run_process_queue_mode
- main

## src/ats/__init__.py
- detect
- get_submitter
- get_ats_registry

## src/ats/csv_applicator.py
- detect
- get_submitter
- apply_from_csv
- main

## src/ats/application_flow_optimizer.py
- optimize_job_application

## src/utils/job_filters.py
- filter_job
- filter_jobs_batch
- get_filter_stats

## src/utils/job_data_consumer.py
- worker_process

## src/utils/job_analysis_engine.py
- run_scraping
- scrape_with_enhanced_scrapers
- get_scraper_for_site
- run_intelligent_scraping

## src/utils/error_tolerance_handler.py
- with_retry
- with_fallback
- circuit_breaker
- safe_execute
- check_database_connection
- check_disk_space
- check_memory_usage
- get_error_tolerance_handler

## src/utils/enhanced_error_tolerance.py
- with_retry
- with_fallback
- safe_execute
- display_error_dashboard

## src/utils/enhanced_database_manager.py
- main
- get_database_manager

## src/utils/document_generator.py
- fix_ssl_cert_path
- customize
- customize_resume_with_fallbacks
- customize_cover_letter_with_fallbacks
- customize_resume_ai_enhanced
- customize_resume_template_based
- customize_resume_basic_replacement
- create_emergency_text_resume
- add_keywords_template_based
- customize_cover_letter_ai_enhanced
- customize_cover_letter_template_based
- customize_cover_letter_basic_replacement
- create_emergency_text_cover_letter
- add_keywords_to_cover_letter_template_based
- customize_resume
- customize_cover_letter
- add_keyword_to_bullet
- add_skills_section
- replace_placeholders
- customize_greeting
- enhance_cover_letter_with_keywords
- flatten_document_styles

## src/dashboard/job_cache.py
- add_job_to_cache
- get_latest_jobs
- get_cache_stats

## src/dashboard/api_v2.py
- create_dashboard_v2

## src/dashboard/api.py
- get_comprehensive_stats
- get_application_stats
- get_recent_logs
- get_pause_status

## src/cli/arg_parser.py
- create_parser
- parse_args
- validate_args

---

*This list is auto-generated. For a full audit, repeat this process after major refactors or new feature additions.* 