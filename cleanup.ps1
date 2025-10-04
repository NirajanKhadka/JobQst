# Cleanup Script for JobLens Repository
# This script removes temporary files and outdated documentation

Write-Host "🧹 JobLens Repository Cleanup Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Safety check
$confirm = Read-Host "This will delete 100+ temporary files. Create backup first? (Y/n)"
if ($confirm -ne 'n' -and $confirm -ne 'N') {
    Write-Host "Creating backup branch..." -ForegroundColor Yellow
    git checkout -b pre-cleanup-backup-$(Get-Date -Format "yyyyMMdd-HHmmss")
    git push origin HEAD
    git checkout main
    Write-Host "✅ Backup created" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting cleanup..." -ForegroundColor Yellow
Write-Host ""

# Phase 1: Remove temporary Python scripts
Write-Host "Phase 1: Removing temporary Python scripts..." -ForegroundColor Cyan

$tempScripts = @(
    "analyze_skipped_tests.py",
    "apply_profile_fixes.py",
    "check_actual_db.py",
    "check_both_dbs.py",
    "check_dashboard_data.py",
    "check_db_columns.py",
    "check_fit_scores.py",
    "check_jobs_now.py",
    "debug_dashboard_callbacks.py",
    "debug_salary_parser.py",
    "demo_config_architecture.py",
    "diagnose_dashboard.py",
    "fix_all_profile_callbacks.py",
    "fix_dashboard_data.py",
    "fix_db_now.py",
    "fix_profile_name_in_db.py",
    "fix_remaining_nirajan.py",
    "focused_dashboard_improvements.py",
    "practical_dashboard_improvements.py",
    "quick_db_check.py",
    "quick_skip_analysis.py",
    "quick_ux_fixes.py",
    "test_callbacks_firing.py",
    "test_cli_fixes.py",
    "test_config_matcher.py",
    "test_dashboard_data_loading.py",
    "test_dashboard_features.py",
    "test_dashboard_fix.py",
    "test_dashboard_fixes.py",
    "test_dashboard_integration.py",
    "test_dashboard_minimal.py",
    "test_dashboard_performance.py",
    "test_dashboard_profile.py",
    "test_dashboard_rendering.py",
    "test_interactive_menu.py",
    "test_k_pattern.py",
    "test_parser_accuracy.py",
    "test_phase2_systems.py",
    "test_phase3_integration.py",
    "test_profile_fix.py",
    "test_ranked_jobs_callback.py",
    "test_task5_implementation.py",
    "verify_dashboard_features.py",
    "verify_dashboard_fix.py",
    "verify_profile_fixes.py"
)

$removed = 0
foreach ($file in $tempScripts) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✓ Removed $file" -ForegroundColor Gray
        $removed++
    }
}
Write-Host "Removed $removed temporary Python scripts" -ForegroundColor Green
Write-Host ""

# Phase 2: Remove redundant documentation
Write-Host "Phase 2: Removing redundant documentation..." -ForegroundColor Cyan

$tempDocs = @(
    "DASHBOARD_99_JOBS_CONFIRMED.md",
    "DASHBOARD_ALL_TABS_ENHANCED.md",
    "DASHBOARD_ARCHITECTURE_ISSUES.md",
    "DASHBOARD_BLANK_PAGE_FIX.md",
    "DASHBOARD_CALLBACK_FIX_COMPLETE.md",
    "DASHBOARD_DEBUG_COMPLETE.md",
    "DASHBOARD_DOCS_INDEX.md",
    "DASHBOARD_ENHANCEMENTS_COMPLETE.md",
    "DASHBOARD_FINAL_FIX.md",
    "DASHBOARD_FIXES_2025_10_04.md",
    "DASHBOARD_FIX_PRIORITY_PLAN.md",
    "DASHBOARD_FIX_SUMMARY.md",
    "DASHBOARD_ISSUES_SUMMARY.md",
    "DASHBOARD_ISSUE_DIAGNOSIS.md",
    "DASHBOARD_NO_DATA_FIX.md",
    "DASHBOARD_PROFILE_FIXES_COMPLETE.md",
    "dashboard_ux_improvements.md",
    "final_dashboard_plan.md",
    "job_seeker_focused_improvements.md",
    "TASK_5_BEFORE_AFTER.md",
    "TASK_5_COMPLETION_SUMMARY.md",
    "TASK_5_FINAL_REPORT.md",
    "TASK_5_HOME_TAB_STRUCTURE.md",
    "TASKS_5_TO_10_COMPLETE_SUMMARY.md",
    "TASKS_6_10_IMPLEMENTATION_SUMMARY.md",
    "TASKS_8_10_ARCHITECTURE.md",
    "TASKS_8_10_COMPLETION_SUMMARY.md",
    "TASKS_8_10_FINAL_CHECKLIST.md",
    "TASKS_11_14_COMPLETION_SUMMARY.md",
    "TASKS_15_17_COMPLETION_SUMMARY.md",
    "TANDAVA_DANCE_COMPLETE.md",
    "PHASE_2_3_COMPLETION_SUMMARY.md",
    "CLEANUP_COMPLETE.md",
    "COMPREHENSIVE_DASHBOARD_IMPROVEMENT_PLAN.md",
    "DOCUMENTATION_CREATION_SUMMARY.md",
    "DUPLICATE_CALLBACK_FIX.md",
    "FIXES_SUMMARY.md",
    "HEALTH_CHECK_FIX_SUMMARY.md",
    "INTERACTIVE_MENU_ENHANCEMENT.md",
    "PROFILE_AND_PARSER_UPDATES.md",
    "PROFILE_FIXES_APPLIED.md",
    "PROFILE_LOADING_FIXED.md",
    "TEST_CLEANUP_SUMMARY.md",
    "TEST_STATUS_REPORT.md",
    "VERIFICATION_REPORT_POSTGRESQL_DOCKER_CLEANUP.md",
    "README.md.backup"
)

$removed = 0
foreach ($file in $tempDocs) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✓ Removed $file" -ForegroundColor Gray
        $removed++
    }
}
Write-Host "Removed $removed redundant documentation files" -ForegroundColor Green
Write-Host ""

# Phase 3: Remove test data
Write-Host "Phase 3: Removing test data..." -ForegroundColor Cyan
if (Test-Path "nirajan") {
    Remove-Item "nirajan" -Recurse -Force
    Write-Host "  ✓ Removed nirajan test data" -ForegroundColor Gray
    Write-Host "Removed test data" -ForegroundColor Green
}
Write-Host ""

# Phase 4: Clean up cache and logs (optional)
Write-Host "Phase 4: Cleaning cache and logs (optional)..." -ForegroundColor Cyan
$cleanCache = Read-Host "Clean cache/ and logs/ directories? (y/N)"
if ($cleanCache -eq 'y' -or $cleanCache -eq 'Y') {
    if (Test-Path "cache") {
        Get-ChildItem "cache" -Recurse | Remove-Item -Force -Recurse
        Write-Host "  ✓ Cleaned cache/" -ForegroundColor Gray
    }
    if (Test-Path "logs") {
        Get-ChildItem "logs" -File | Remove-Item -Force
        Write-Host "  ✓ Cleaned logs/" -ForegroundColor Gray
    }
    Write-Host "Cache and logs cleaned" -ForegroundColor Green
} else {
    Write-Host "Skipped cache/logs cleanup" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "✅ Cleanup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review changes: git status" -ForegroundColor White
Write-Host "2. Test application: python main.py <profile> --action health-check" -ForegroundColor White
Write-Host "3. Commit changes: git add -A && git commit -m 'chore: cleanup temporary files'" -ForegroundColor White
Write-Host "4. Push changes: git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "Files kept:" -ForegroundColor Cyan
Write-Host "  ✓ create_new_profile.py (utility)" -ForegroundColor Green
Write-Host "  ✓ README.md (main docs)" -ForegroundColor Green
Write-Host "  ✓ QUICK_REFERENCE.md (user guide)" -ForegroundColor Green
Write-Host "  ✓ DASHBOARD_COMPLETE_GUIDE.md" -ForegroundColor Green
Write-Host "  ✓ DASHBOARD_QUICK_REFERENCE.md" -ForegroundColor Green
Write-Host "  ✓ HEALTH_CHECK_AND_PROFILE_GUIDE.md" -ForegroundColor Green
Write-Host "  ✓ docs/ directory (all files)" -ForegroundColor Green
Write-Host ""
