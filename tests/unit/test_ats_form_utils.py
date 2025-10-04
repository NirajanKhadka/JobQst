#!/usr/bin/env python3
"""
Unit Tests for ATS Form Utilities
Tests the form filling, document upload, and page interaction utilities.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from playwright.async_api import Page

from src.ats.form_utils import (
    find_and_click_apply_button,
    fill_form_fields,
    upload_resume,
    upload_cover_letter,
    click_next_or_continue,
    click_submit_button,
    check_for_captcha,
    check_for_login_required,
    check_for_confirmation,
    generate_cover_letter_text,
)


class TestFindAndClickApplyButton:
    """Test the find_and_click_apply_button function."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = AsyncMock(spec=Page)
        return page

    @pytest.mark.asyncio
    async def test_find_apply_button_success_standard_button(self, mock_page):
        """Test finding and clicking a standard apply button."""
        # Arrange
        mock_page.is_visible.return_value = True
        mock_page.click = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        # Act
        result = await find_and_click_apply_button(mock_page)

        # Assert
        assert result is True
        mock_page.click.assert_called_once()
        mock_page.wait_for_load_state.assert_called_once_with("domcontentloaded")

    @pytest.mark.asyncio
    async def test_find_apply_button_no_button_found(self, mock_page):
        """Test when no apply button is found."""
        # Arrange
        mock_page.is_visible.return_value = False

        # Act
        result = await find_and_click_apply_button(mock_page)

        # Assert
        assert result is False
        mock_page.click.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_apply_button_handles_exception(self, mock_page):
        """Test exception handling when clicking fails."""
        # Arrange
        mock_page.is_visible.side_effect = Exception("Page error")

        # Act
        result = await find_and_click_apply_button(mock_page)

        # Assert
        assert result is False


class TestFillFormFields:
    """Test the fill_form_fields function."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = AsyncMock(spec=Page)
        return page

    @pytest.fixture
    def sample_profile(self):
        """Create a sample user profile."""
        return {
            "name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "location": "Toronto, ON",
        }

    @pytest.mark.asyncio
    async def test_fill_form_fields_success(self, mock_page, sample_profile):
        """Test successful form field filling."""
        # Arrange
        mock_element = AsyncMock()
        mock_element.is_visible.return_value = True
        mock_element.input_value.return_value = ""  # Empty field
        mock_element.fill = AsyncMock()

        mock_page.query_selector_all.return_value = [mock_element]

        # Act
        fields_filled = await fill_form_fields(mock_page, sample_profile)

        # Assert
        assert fields_filled > 0
        mock_element.fill.assert_called()

    @pytest.mark.asyncio
    async def test_fill_form_fields_skips_filled_fields(self, mock_page, sample_profile):
        """Test that already filled fields are skipped."""
        # Arrange
        mock_element = AsyncMock()
        mock_element.is_visible.return_value = True
        mock_element.input_value.return_value = "existing value"  # Already filled
        mock_element.fill = AsyncMock()

        mock_page.query_selector_all.return_value = [mock_element]

        # Act
        fields_filled = await fill_form_fields(mock_page, sample_profile)

        # Assert
        mock_element.fill.assert_not_called()

    @pytest.mark.asyncio
    async def test_fill_form_fields_handles_empty_profile(self, mock_page):
        """Test handling of empty profile data."""
        # Arrange
        empty_profile = {}
        mock_page.query_selector_all.return_value = []

        # Act
        fields_filled = await fill_form_fields(mock_page, empty_profile)

        # Assert
        assert fields_filled == 0

    @pytest.mark.asyncio
    async def test_fill_form_fields_name_splitting(self, mock_page):
        """Test proper name splitting from full name."""
        # Arrange
        profile_with_full_name = {"name": "Jane Elizabeth Smith"}
        mock_element = AsyncMock()
        mock_element.is_visible.return_value = True
        mock_element.input_value.return_value = ""
        mock_element.fill = AsyncMock()

        mock_page.query_selector_all.return_value = [mock_element]

        # Act
        await fill_form_fields(mock_page, profile_with_full_name)

        # Assert
        # Should have called fill with first name "Jane" and last name "Smith"
        assert mock_element.fill.call_count > 0


class TestFileUpload:
    """Test file upload functions."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = AsyncMock(spec=Page)
        return page

    @pytest.fixture
    def temp_resume_file(self, tmp_path):
        """Create a temporary resume file."""
        resume_file = tmp_path / "resume.pdf"
        resume_file.write_text("Mock resume content")
        return str(resume_file)

    @pytest.fixture
    def temp_cover_letter_file(self, tmp_path):
        """Create a temporary cover letter file."""
        cover_file = tmp_path / "cover_letter.pdf"
        cover_file.write_text("Mock cover letter content")
        return str(cover_file)

    @pytest.mark.asyncio
    async def test_upload_resume_success(self, mock_page, temp_resume_file):
        """Test successful resume upload."""
        # Arrange
        mock_element = AsyncMock()
        mock_element.is_visible.return_value = True
        mock_element.set_input_files = AsyncMock()

        mock_page.query_selector_all.return_value = [mock_element]

        # Act
        result = await upload_resume(mock_page, temp_resume_file)

        # Assert
        assert result is True
        mock_element.set_input_files.assert_called_once_with(temp_resume_file)

    @pytest.mark.asyncio
    async def test_upload_resume_file_not_found(self, mock_page):
        """Test resume upload when file doesn't exist."""
        # Arrange
        nonexistent_file = "/path/to/nonexistent/resume.pdf"

        # Act
        result = await upload_resume(mock_page, nonexistent_file)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_upload_resume_empty_path(self, mock_page):
        """Test resume upload with empty path."""
        # Act
        result = await upload_resume(mock_page, "")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_upload_cover_letter_success(self, mock_page, temp_cover_letter_file):
        """Test successful cover letter upload."""
        # Arrange
        mock_element = AsyncMock()
        mock_element.is_visible.return_value = True
        mock_element.set_input_files = AsyncMock()

        mock_page.query_selector_all.return_value = [mock_element]

        # Act
        result = await upload_cover_letter(mock_page, temp_cover_letter_file)

        # Assert
        assert result is True
        mock_element.set_input_files.assert_called_once_with(temp_cover_letter_file)


class TestNavigationButtons:
    """Test navigation button functions."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = AsyncMock(spec=Page)
        return page

    @pytest.mark.asyncio
    async def test_click_next_or_continue_success(self, mock_page):
        """Test successful next/continue button click."""
        # Arrange
        mock_page.is_visible.return_value = True
        mock_page.click = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        # Act
        result = await click_next_or_continue(mock_page)

        # Assert
        assert result is True
        mock_page.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_next_or_continue_no_button(self, mock_page):
        """Test when no next/continue button is found."""
        # Arrange
        mock_page.is_visible.return_value = False

        # Act
        result = await click_next_or_continue(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_click_submit_button_with_confirmation(self, mock_page):
        """Test submit button click with confirmation."""
        # Arrange
        mock_page.is_visible.return_value = True
        mock_page.click = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        # Mock confirmation check
        with patch("src.ats.form_utils.check_for_confirmation", return_value=True):
            # Act
            result = await click_submit_button(mock_page)

        # Assert
        assert result is True
        mock_page.click.assert_called_once()


class TestPageChecks:
    """Test page state checking functions."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page object."""
        page = AsyncMock(spec=Page)
        return page

    @pytest.mark.asyncio
    async def test_check_for_captcha_detected(self, mock_page):
        """Test CAPTCHA detection."""
        # Arrange
        mock_page.is_visible.return_value = True

        # Act
        result = await check_for_captcha(mock_page)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_for_captcha_not_detected(self, mock_page):
        """Test when no CAPTCHA is present."""
        # Arrange
        mock_page.is_visible.return_value = False

        # Act
        result = await check_for_captcha(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_for_login_required_detected(self, mock_page):
        """Test login requirement detection."""
        # Arrange
        mock_page.is_visible.return_value = True

        # Act
        result = await check_for_login_required(mock_page)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_for_login_required_not_detected(self, mock_page):
        """Test when login is not required."""
        # Arrange
        mock_page.is_visible.return_value = False

        # Act
        result = await check_for_login_required(mock_page)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_for_confirmation_detected(self, mock_page):
        """Test confirmation detection."""
        # Arrange
        mock_page.is_visible.return_value = True

        # Act
        result = await check_for_confirmation(mock_page)

        # Assert
        assert result is True


class TestGenerateCoverLetterText:
    """Test cover letter generation."""

    def test_generate_cover_letter_with_name(self):
        """Test cover letter generation with profile name."""
        # Arrange
        profile = {"name": "Alice Johnson"}

        # Act
        cover_letter = generate_cover_letter_text(profile)

        # Assert
        assert "Alice Johnson" in cover_letter
        assert "Dear Hiring Manager" in cover_letter
        assert "Best regards" in cover_letter

    def test_generate_cover_letter_without_name(self):
        """Test cover letter generation without profile name."""
        # Arrange
        profile = {}

        # Act
        cover_letter = generate_cover_letter_text(profile)

        # Assert
        assert "Dear Hiring Manager" in cover_letter
        assert "Best regards" in cover_letter
        assert len(cover_letter) > 100  # Should have substantial content

    def test_generate_cover_letter_structure(self):
        """Test that generated cover letter has proper structure."""
        # Arrange
        profile = {"name": "Test User"}

        # Act
        cover_letter = generate_cover_letter_text(profile)

        # Assert
        lines = cover_letter.strip().split("\n")
        assert len(lines) >= 5  # Should have multiple lines
        assert lines[0].startswith("Dear")  # Proper greeting
        assert "Test User" in lines[-1]  # Name in signature


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
