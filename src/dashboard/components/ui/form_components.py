"""
Form Components

This module provides standardized form input components with consistent styling
and validation for the dashboard.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, date, time
import re


class FormInput:
    """Reusable text input component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 value: str = "",
                 placeholder: Optional[str] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False,
                 max_chars: Optional[int] = None,
                 password: bool = False,
                 validator: Optional[Callable[[str], Union[bool, str]]] = None):
        """
        Initialize form input.
        
        Args:
            key: Unique key for the input
            label: Input label
            value: Default value
            placeholder: Placeholder text
            help_text: Help tooltip text
            disabled: Whether input is disabled
            max_chars: Maximum character limit
            password: Whether to hide input (password field)
            validator: Validation function that returns True or error message
        """
        self.key = key
        self.label = label
        self.value = value
        self.placeholder = placeholder
        self.help_text = help_text
        self.disabled = disabled
        self.max_chars = max_chars
        self.password = password
        self.validator = validator
    
    def render(self, container: Optional[Any] = None) -> str:
        """Render the input and return its value."""
        target = container or st
        
        # Choose input type
        if self.password:
            input_value = target.text_input(
                label=self.label,
                value=self.value,
                placeholder=self.placeholder,
                help=self.help_text,
                disabled=self.disabled,
                max_chars=self.max_chars,
                key=self.key,
                type="password"
            )
        else:
            input_value = target.text_input(
                label=self.label,
                value=self.value,
                placeholder=self.placeholder,
                help=self.help_text,
                disabled=self.disabled,
                max_chars=self.max_chars,
                key=self.key
            )
        
        # Validate input
        if self.validator and input_value:
            validation_result = self.validator(input_value)
            if validation_result is not True:
                error_msg = validation_result if isinstance(validation_result, str) else "Invalid input"
                target.error(error_msg)
        
        return input_value


class FormSelect:
    """Reusable select box component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 options: List[Any],
                 index: int = 0,
                 format_func: Optional[Callable] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False):
        """
        Initialize form select.
        
        Args:
            key: Unique key for the select
            label: Select label
            options: List of options
            index: Default selected index
            format_func: Function to format option display
            help_text: Help tooltip text
            disabled: Whether select is disabled
        """
        self.key = key
        self.label = label
        self.options = options
        self.index = index
        self.format_func = format_func
        self.help_text = help_text
        self.disabled = disabled
    
    def render(self, container: Optional[Any] = None) -> Any:
        """Render the select box and return selected value."""
        target = container or st
        
        return target.selectbox(
            label=self.label,
            options=self.options,
            index=self.index,
            format_func=self.format_func,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )


class FormButton:
    """Reusable button component."""
    
    def __init__(self,
                 label: str,
                 key: Optional[str] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False,
                 button_type: str = "primary",
                 use_container_width: bool = False,
                 on_click: Optional[Callable] = None):
        """
        Initialize form button.
        
        Args:
            label: Button label
            key: Unique key for the button
            help_text: Help tooltip text
            disabled: Whether button is disabled
            button_type: Button type ('primary' or 'secondary')
            use_container_width: Whether to use full container width
            on_click: Callback function when clicked
        """
        self.label = label
        self.key = key
        self.help_text = help_text
        self.disabled = disabled
        self.button_type = button_type
        self.use_container_width = use_container_width
        self.on_click = on_click
    
    def render(self, container: Optional[Any] = None) -> bool:
        """Render the button and return click status."""
        target = container or st
        
        clicked = target.button(
            label=self.label,
            key=self.key,
            help=self.help_text,
            disabled=self.disabled,
            type=self.button_type,
            use_container_width=self.use_container_width
        )
        
        if clicked and self.on_click:
            self.on_click()
        
        return clicked


class FormCheckbox:
    """Reusable checkbox component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 value: bool = False,
                 help_text: Optional[str] = None,
                 disabled: bool = False):
        """
        Initialize form checkbox.
        
        Args:
            key: Unique key for the checkbox
            label: Checkbox label
            value: Default value
            help_text: Help tooltip text
            disabled: Whether checkbox is disabled
        """
        self.key = key
        self.label = label
        self.value = value
        self.help_text = help_text
        self.disabled = disabled
    
    def render(self, container: Optional[Any] = None) -> bool:
        """Render the checkbox and return its value."""
        target = container or st
        
        return target.checkbox(
            label=self.label,
            value=self.value,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )


class FormRadio:
    """Reusable radio button component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 options: List[Any],
                 index: int = 0,
                 format_func: Optional[Callable] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False,
                 horizontal: bool = False):
        """
        Initialize form radio buttons.
        
        Args:
            key: Unique key for the radio
            label: Radio group label
            options: List of options
            index: Default selected index
            format_func: Function to format option display
            help_text: Help tooltip text
            disabled: Whether radio is disabled
            horizontal: Whether to display horizontally
        """
        self.key = key
        self.label = label
        self.options = options
        self.index = index
        self.format_func = format_func
        self.help_text = help_text
        self.disabled = disabled
        self.horizontal = horizontal
    
    def render(self, container: Optional[Any] = None) -> Any:
        """Render the radio buttons and return selected value."""
        target = container or st
        
        return target.radio(
            label=self.label,
            options=self.options,
            index=self.index,
            format_func=self.format_func,
            help=self.help_text,
            disabled=self.disabled,
            horizontal=self.horizontal,
            key=self.key
        )


class FormTextarea:
    """Reusable text area component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 value: str = "",
                 placeholder: Optional[str] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False,
                 max_chars: Optional[int] = None,
                 height: Optional[int] = None):
        """
        Initialize form textarea.
        
        Args:
            key: Unique key for the textarea
            label: Textarea label
            value: Default value
            placeholder: Placeholder text
            help_text: Help tooltip text
            disabled: Whether textarea is disabled
            max_chars: Maximum character limit
            height: Height in pixels
        """
        self.key = key
        self.label = label
        self.value = value
        self.placeholder = placeholder
        self.help_text = help_text
        self.disabled = disabled
        self.max_chars = max_chars
        self.height = height
    
    def render(self, container: Optional[Any] = None) -> str:
        """Render the textarea and return its value."""
        target = container or st
        
        return target.text_area(
            label=self.label,
            value=self.value,
            placeholder=self.placeholder,
            help=self.help_text,
            disabled=self.disabled,
            max_chars=self.max_chars,
            height=self.height,
            key=self.key
        )


class FormDatePicker:
    """Reusable date picker component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 value: Optional[date] = None,
                 min_value: Optional[date] = None,
                 max_value: Optional[date] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False):
        """
        Initialize form date picker.
        
        Args:
            key: Unique key for the date picker
            label: Date picker label
            value: Default value
            min_value: Minimum selectable date
            max_value: Maximum selectable date
            help_text: Help tooltip text
            disabled: Whether date picker is disabled
        """
        self.key = key
        self.label = label
        self.value = value or date.today()
        self.min_value = min_value
        self.max_value = max_value
        self.help_text = help_text
        self.disabled = disabled
    
    def render(self, container: Optional[Any] = None) -> date:
        """Render the date picker and return selected date."""
        target = container or st
        
        return target.date_input(
            label=self.label,
            value=self.value,
            min_value=self.min_value,
            max_value=self.max_value,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )


class FormNumberInput:
    """Reusable number input component."""
    
    def __init__(self,
                 key: str,
                 label: str,
                 value: Union[int, float] = 0,
                 min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None,
                 step: Union[int, float] = 1,
                 format_string: Optional[str] = None,
                 help_text: Optional[str] = None,
                 disabled: bool = False):
        """
        Initialize form number input.
        
        Args:
            key: Unique key for the number input
            label: Number input label
            value: Default value
            min_value: Minimum value
            max_value: Maximum value
            step: Step size for increment/decrement
            format_string: Format string for display
            help_text: Help tooltip text
            disabled: Whether number input is disabled
        """
        self.key = key
        self.label = label
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.format_string = format_string
        self.help_text = help_text
        self.disabled = disabled
    
    def render(self, container: Optional[Any] = None) -> Union[int, float]:
        """Render the number input and return its value."""
        target = container or st
        
        return target.number_input(
            label=self.label,
            value=self.value,
            min_value=self.min_value,
            max_value=self.max_value,
            step=self.step,
            format=self.format_string,
            help=self.help_text,
            disabled=self.disabled,
            key=self.key
        )


# Validation functions
def validate_email(email: str) -> Union[bool, str]:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return "Please enter a valid email address"


def validate_phone(phone: str) -> Union[bool, str]:
    """Validate phone number format."""
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    
    # Check for valid length and digits
    if len(cleaned) >= 10 and cleaned.isdigit():
        return True
    return "Please enter a valid phone number"


def validate_url(url: str) -> Union[bool, str]:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    if re.match(pattern, url):
        return True
    return "Please enter a valid URL"


def validate_non_empty(text: str) -> Union[bool, str]:
    """Validate non-empty text."""
    if text.strip():
        return True
    return "This field is required"


def validate_min_length(min_length: int):
    """Create a minimum length validator."""
    def validator(text: str) -> Union[bool, str]:
        if len(text) >= min_length:
            return True
        return f"Minimum length is {min_length} characters"
    return validator


# Convenience functions for quick form creation
def text_input(key: str, label: str, **kwargs) -> str:
    """Quick text input creation."""
    input_field = FormInput(key, label, **kwargs)
    return input_field.render()


def select_box(key: str, label: str, options: List[Any], **kwargs) -> Any:
    """Quick select box creation."""
    select_field = FormSelect(key, label, options, **kwargs)
    return select_field.render()


def button(label: str, **kwargs) -> bool:
    """Quick button creation."""
    button_field = FormButton(label, **kwargs)
    return button_field.render()


def checkbox(key: str, label: str, **kwargs) -> bool:
    """Quick checkbox creation."""
    checkbox_field = FormCheckbox(key, label, **kwargs)
    return checkbox_field.render()


def text_area(key: str, label: str, **kwargs) -> str:
    """Quick text area creation."""
    textarea_field = FormTextarea(key, label, **kwargs)
    return textarea_field.render()


def number_input(key: str, label: str, **kwargs) -> Union[int, float]:
    """Quick number input creation."""
    number_field = FormNumberInput(key, label, **kwargs)
    return number_field.render()
