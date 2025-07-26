#!/usr/bin/env python3
"""
Unit Tests for ATS Handlers
Tests the ATS-specific application handlers (Workday, Greenhouse, etc.).
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from playwright.async_api import Page, BrowserContext

from src.ats.workday_handler import apply_workday
from src.ats.greenhouse_handler import apply_greenhouse
from src.ats.icims_handler import apply_icims
from src.ats.lever_handler import apply_lever
from src.ats.bamboohr_handler import apply_bamboohr


class TestWorkdayHandler:
    """Test the Workday ATS handler."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object with context."""
        page = AsyncMock(spec=Page)
        context = AsyncMock(spec=BrowserContext)
        page.context = context
        
        # Mock profile data
        context._profile = {
            "name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "location": "Toronto, ON",
        }
        context._resume_path = "/path/to/resume.pdf"
        context._cover_letter_path = "/path/to/cover_letter.pdf"
        
        return page

    @pytest.fixture
    def sample_job(self):
        """Create a sample job dictionary."""
        return {
            "id": "workday_job_123",
            "title": "Software Engineer",
            "company": "Tech Corp",
            "url": "https://techcorp.wd1.myworkdayjobs.com/careers/job/123",
            "location": "Toronto, ON",
        }

    @pytest.mark.asyncio
    async def test_apply_workday_success_path(self, mock_page, sample_job):
        """Test successful Workday application."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.workday_handler.check_for_captcha', return_value=False), \
             patch('src.ats.workday_handler.check_for_login_required', return_value=False), \
             patch('src.ats.workday_handler.fill_form_fields', return_value=3), \
             patch('src.ats.workday_handler.upload_resume', return_value=True), \
             patch('src.ats.workday_handler.upload_cover_letter', return_value=True), \
             patch('src.ats.workday_handler.click_next_or_continue', return_value=False), \
             patch('src.ats.workday_handler.click_submit_button', return_value=True):

            # Act
            result = await apply_workday(mock_page, sample_job)

        # Assert
        assert result == "applied"

    @pytest.mark.asyncio
    async def test_apply_workday_no_apply_button(self, mock_page, sample_job):
        """Test Workday application when no apply button is found."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=False):
            # Act
            result = await apply_workday(mock_page, sample_job)

        # Assert
        assert result == "no_apply_button"

    @pytest.mark.asyncio
    async def test_apply_workday_captcha_detected(self, mock_page, sample_job):
        """Test Workday application when CAPTCHA is detected."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.workday_handler.check_for_captcha', return_value=True):

            # Act
            result = await apply_workday(mock_page, sample_job)

        # Assert
        assert result == "captcha_detected"

    @pytest.mark.asyncio
    async def test_apply_workday_login_required(self, mock_page, sample_job):
        """Test Workday application when login is required."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.workday_handler.check_for_captcha', return_value=False), \
             patch('src.ats.workday_handler.check_for_login_required', return_value=True):

            # Act
            result = await apply_workday(mock_page, sample_job)

        # Assert
        assert result == "login_required"

    @pytest.mark.asyncio
    async def test_apply_workday_manual_completion(self, mock_page, sample_job):
        """Test Workday application requiring manual completion."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.workday_handler.check_for_captcha', return_value=False), \
             patch('src.ats.workday_handler.check_for_login_required', return_value=False), \
             patch('src.ats.workday_handler.fill_form_fields', return_value=2), \
             patch('src.ats.workday_handler.upload_resume', return_value=True), \
             patch('src.ats.workday_handler.upload_cover_letter', return_value=False), \
             patch('src.ats.workday_handler.click_next_or_continue', return_value=False), \
             patch('src.ats.workday_handler.click_submit_button', return_value=False):

            # Act
            result = await apply_workday(mock_page, sample_job)

        # Assert
        assert result == "manual"

    @pytest.mark.asyncio
    async def test_apply_workday_exception_handling(self, mock_page, sample_job):
        """Test Workday application exception handling."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', side_effect=Exception("Test error")):
            # Act
            result = await apply_workday(mock_page, sample_job)

        # Assert
        assert result.startswith("error:")
        assert "Test error" in result

    @pytest.mark.asyncio
    async def test_apply_workday_uses_profile_data(self, mock_page, sample_job):
        """Test that Workday handler uses profile data from context."""
        # Arrange
        with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.workday_handler.check_for_captcha', return_value=False), \
             patch('src.ats.workday_handler.check_for_login_required', return_value=False), \
             patch('src.ats.workday_handler.fill_form_fields') as mock_fill, \
             patch('src.ats.workday_handler.upload_resume') as mock_upload_resume, \
             patch('src.ats.workday_handler.upload_cover_letter') as mock_upload_cover, \
             patch('src.ats.workday_handler.click_next_or_continue', return_value=False), \
             patch('src.ats.workday_handler.click_submit_button', return_value=True):

            mock_fill.return_value = 3
            mock_upload_resume.return_value = True
            mock_upload_cover.return_value = True

            # Act
            result = await apply_workday(mock_page, sample_job)

            # Assert
            assert result == "applied"
            # Verify that profile data was passed correctly
            mock_fill.assert_called_once()
            mock_upload_resume.assert_called_with(mock_page, "/path/to/resume.pdf")
            mock_upload_cover.assert_called_with(mock_page, "/path/to/cover_letter.pdf")


class TestGreenhouseHandler:
    """Test the Greenhouse ATS handler."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object with context."""
        page = AsyncMock(spec=Page)
        context = AsyncMock(spec=BrowserContext)
        page.context = context
        
        context._profile = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
        }
        context._resume_path = "/path/to/resume.pdf"
        context._cover_letter_path = ""
        
        return page

    @pytest.fixture
    def sample_job(self):
        """Create a sample job dictionary."""
        return {
            "id": "greenhouse_job_456",
            "title": "Data Scientist",
            "company": "Data Corp",
            "url": "https://boards.greenhouse.io/datacorp/jobs/456",
        }

    @pytest.mark.asyncio
    async def test_apply_greenhouse_success_path(self, mock_page, sample_job):
        """Test successful Greenhouse application."""
        # Arrange
        with patch('src.ats.greenhouse_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.greenhouse_handler.check_for_captcha', return_value=False), \
             patch('src.ats.greenhouse_handler.check_for_login_required', return_value=False), \
             patch('src.ats.greenhouse_handler.fill_form_fields', return_value=2), \
             patch('src.ats.greenhouse_handler.upload_resume', return_value=True), \
             patch('src.ats.greenhouse_handler.upload_cover_letter', return_value=False), \
             patch('src.ats.greenhouse_handler.click_next_or_continue', return_value=False), \
             patch('src.ats.greenhouse_handler.click_submit_button', return_value=True):

            # Act
            result = await apply_greenhouse(mock_page, sample_job)

        # Assert
        assert result == "applied"

    @pytest.mark.asyncio
    async def test_apply_greenhouse_no_cover_letter(self, mock_page, sample_job):
        """Test Greenhouse application without cover letter."""
        # Arrange - mock page context has empty cover letter path
        mock_page.context._cover_letter_path = ""
        
        with patch('src.ats.greenhouse_handler.find_and_click_apply_button', return_value=True), \
             patch('src.ats.greenhouse_handler.check_for_captcha', return_value=False), \
             patch('src.ats.greenhouse_handler.check_for_login_required', return_value=False), \
             patch('src.ats.greenhouse_handler.fill_form_fields', return_value=2), \
             patch('src.ats.greenhouse_handler.upload_resume', return_value=True), \
             patch('src.ats.greenhouse_handler.upload_cover_letter') as mock_cover, \
             patch('src.ats.greenhouse_handler.click_next_or_continue', return_value=False), \
             patch('src.ats.greenhouse_handler.click_submit_button', return_value=True):

            # Act
            result = await apply_greenhouse(mock_page, sample_job)

        # Assert
        assert result == "applied"
        # Should not attempt to upload cover letter when path is empty
        mock_cover.assert_not_called()


class TestFallbackHandlers:
    """Test the fallback ATS handlers (iCIMS, Lever, BambooHR)."""

    @pytest.fixture
    def mock_page_with_generic(self):
        """Create a mock page with generic apply function."""
        page = AsyncMock(spec=Page)
        context = AsyncMock(spec=BrowserContext)
        page.context = context
        
        # Mock generic apply function
        async def mock_generic_apply(page, job):
            return "applied"
        
        context._generic_apply = mock_generic_apply
        return page

    @pytest.fixture
    def mock_page_without_generic(self):
        """Create a mock page without generic apply function."""
        page = AsyncMock(spec=Page)
        context = AsyncMock(spec=BrowserContext)
        page.context = context
        # No _generic_apply attribute
        return page

    @pytest.fixture
    def sample_job(self):
        """Create a sample job dictionary."""
        return {
            "id": "test_job_789",
            "title": "Product Manager",
            "company": "Product Corp",
            "url": "https://example.com/jobs/789",
        }

    @pytest.mark.asyncio
    async def test_apply_icims_with_generic(self, mock_page_with_generic, sample_job):
        """Test iCIMS handler with generic apply function."""
        # Act
        result = await apply_icims(mock_page_with_generic, sample_job)

        # Assert
        assert result == "applied"

    @pytest.mark.asyncio
    async def test_apply_icims_without_generic(self, mock_page_without_generic, sample_job):
        """Test iCIMS handler without generic apply function."""
        # Act
        result = await apply_icims(mock_page_without_generic, sample_job)

        # Assert
        assert result == "error: generic_apply not available"

    @pytest.mark.asyncio
    async def test_apply_lever_with_generic(self, mock_page_with_generic, sample_job):
        """Test Lever handler with generic apply function."""
        # Act
        result = await apply_lever(mock_page_with_generic, sample_job)

        # Assert
        assert result == "applied"

    @pytest.mark.asyncio
    async def test_apply_bamboohr_with_generic(self, mock_page_with_generic, sample_job):
        """Test BambooHR handler with generic apply function."""
        # Act
        result = await apply_bamboohr(mock_page_with_generic, sample_job)

        # Assert
        assert result == "applied"


class TestHandlerIntegration:
    """Integration tests for ATS handlers."""

    @pytest.mark.asyncio
    async def test_all_handlers_have_consistent_interface(self):
        """Test that all handlers have consistent function signatures."""
        # Arrange
        mock_page = AsyncMock(spec=Page)
        mock_page.context = AsyncMock(spec=BrowserContext)
        mock_page.context._generic_apply = AsyncMock(return_value="applied")
        
        sample_job = {
            "id": "test_job",
            "title": "Test Job",
            "company": "Test Company",
            "url": "https://example.com/job",
        }

        handlers = [
            apply_workday,
            apply_greenhouse,
            apply_icims,
            apply_lever,
            apply_bamboohr,
        ]

        # Act & Assert
        for handler in handlers:
            # Should not raise any exceptions about function signature
            try:
                with patch('src.ats.workday_handler.find_and_click_apply_button', return_value=False), \
                     patch('src.ats.greenhouse_handler.find_and_click_apply_button', return_value=False):
                    result = await handler(mock_page, sample_job)
                    # Should return a string result
                    assert isinstance(result, str)
            except Exception as e:
                pytest.fail(f"Handler {handler.__name__} failed with: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
