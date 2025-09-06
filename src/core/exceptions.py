"""
Custom exceptions for AutoJobAgent.
"""


class AutoJobAgentError(Exception):
    """Base exception for AutoJobAgent."""

    pass


class ScrapingError(AutoJobAgentError):
    """Exception raised when scraping fails."""

    pass


class DatabaseError(AutoJobAgentError):
    """Exception raised when database operations fail."""

    pass


class ConfigurationError(AutoJobAgentError):
    """Exception raised when configuration is invalid."""

    pass


class AuthenticationError(AutoJobAgentError):
    """Exception raised when authentication fails."""

    pass


class NetworkError(AutoJobAgentError):
    """Exception raised when network operations fail."""

    pass


class ValidationError(AutoJobAgentError):
    """Exception raised when data validation fails."""

    pass


class JobApplicationError(AutoJobAgentError):
    """Exception raised when job application fails."""

    pass


class BrowserError(AutoJobAgentError):
    """Exception raised when browser operations fail."""

    pass


class RateLimitError(AutoJobAgentError):
    """Exception raised when rate limit is exceeded."""

    pass


class TimeoutError(AutoJobAgentError):
    """Exception raised when operations timeout."""

    pass


class FileOperationError(AutoJobAgentError):
    """Exception raised when file operations fail."""

    pass


class ProfileError(AutoJobAgentError):
    """Exception raised when profile operations fail."""

    pass


class DashboardError(AutoJobAgentError):
    """Exception raised when dashboard operations fail."""

    pass


class ATSIntegrationError(AutoJobAgentError):
    """Exception raised when ATS integration fails."""

    pass


class EmailError(AutoJobAgentError):
    """Exception raised when email operations fail."""

    pass


class ResumeError(AutoJobAgentError):
    """Exception raised when resume operations fail."""

    pass


class JobFilterError(AutoJobAgentError):
    """Exception raised when job filtering fails."""

    pass


class SessionError(AutoJobAgentError):
    """Exception raised when session management fails."""

    pass


class TabManagementError(AutoJobAgentError):
    """Exception raised when tab management fails."""

    pass


class PopupHandlingError(AutoJobAgentError):
    """Exception raised when popup handling fails."""

    pass


class NeedsHumanException(AutoJobAgentError):
    """Exception raised when human intervention is required."""

    pass

