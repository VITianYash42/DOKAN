"""
Centralized input validation layer for Dokan Flask application.

This module provides reusable validation functions to ensure data integrity
and prevent server errors from malformed input across all routes.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import re


class ValidationError(Exception):
    """Custom exception for validation errors with field information."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, str]:
        """Convert validation error to dictionary format."""
        return {
            'error': self.message,
            'field': self.field
        }


def require_fields(data: Dict[str, Any], fields: List[str]) -> None:
    """
    Validate that all required fields are present and non-empty in the data.

    Args:
        data: Dictionary containing form/request data
        fields: List of required field names

    Raises:
        ValidationError: If any required field is missing or empty
    """
    for field in fields:
        if field not in data:
            raise ValidationError(f"Required field '{field}' is missing", field)

        value = data[field]
        # Check for None, empty string, or whitespace-only string
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"Field '{field}' cannot be empty", field)


def parse_int(name: str, value: Any, min_val: Optional[int] = None,
              max_val: Optional[int] = None) -> int:
    """
    Parse and validate an integer value with optional range constraints.

    Args:
        name: Field name for error messages
        value: Value to parse
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Returns:
        Validated integer value

    Raises:
        ValidationError: If value cannot be parsed or is out of range
    """
    try:
        parsed_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"Field '{name}' must be a valid integer", name)

    if min_val is not None and parsed_value < min_val:
        raise ValidationError(
            f"Field '{name}' must be at least {min_val}", name
        )

    if max_val is not None and parsed_value > max_val:
        raise ValidationError(
            f"Field '{name}' must be at most {max_val}", name
        )

    return parsed_value


def parse_float(name: str, value: Any, min_val: Optional[float] = None,
                max_val: Optional[float] = None, decimals: Optional[int] = None) -> float:
    """
    Parse and validate a float value with optional range and precision constraints.

    Args:
        name: Field name for error messages
        value: Value to parse
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        decimals: Maximum number of decimal places allowed

    Returns:
        Validated float value

    Raises:
        ValidationError: If value cannot be parsed or is out of range
    """
    try:
        parsed_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"Field '{name}' must be a valid number", name)

    # Check for invalid float values
    if not (-float('inf') < parsed_value < float('inf')):
        raise ValidationError(f"Field '{name}' must be a valid number", name)

    if min_val is not None and parsed_value < min_val:
        raise ValidationError(
            f"Field '{name}' must be at least {min_val}", name
        )

    if max_val is not None and parsed_value > max_val:
        raise ValidationError(
            f"Field '{name}' must be at most {max_val}", name
        )

    if decimals is not None:
        # Round to specified decimals
        parsed_value = round(parsed_value, decimals)

    return parsed_value


def validate_gst(value: Any, field_name: str = "GST") -> float:
    """
    Validate GST percentage value.

    In India, GST rates are typically: 0%, 5%, 12%, 18%, 28%
    This validator accepts any value between 0% and 50% for flexibility.

    Args:
        value: GST percentage value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated GST value

    Raises:
        ValidationError: If GST value is invalid
    """
    gst_value = parse_float(field_name, value, min_val=0.0, max_val=50.0, decimals=2)
    return gst_value


def validate_string(name: str, value: Any, min_length: int = 1,
                    max_length: Optional[int] = None,
                    pattern: Optional[str] = None,
                    trim: bool = True) -> str:
    """
    Validate and normalize string input.

    Args:
        name: Field name for error messages
        value: Value to validate
        min_length: Minimum string length
        max_length: Maximum string length
        pattern: Optional regex pattern to match
        trim: Whether to trim whitespace

    Returns:
        Validated and normalized string

    Raises:
        ValidationError: If string validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"Field '{name}' must be a text value", name)

    # Trim whitespace if requested
    validated_value = value.strip() if trim else value

    # Check length constraints
    if len(validated_value) < min_length:
        raise ValidationError(
            f"Field '{name}' must be at least {min_length} character(s) long", name
        )

    if max_length is not None and len(validated_value) > max_length:
        raise ValidationError(
            f"Field '{name}' must be at most {max_length} characters long", name
        )

    # Check pattern if provided
    if pattern is not None and not re.match(pattern, validated_value):
        raise ValidationError(
            f"Field '{name}' has an invalid format", name
        )

    return validated_value


def validate_date(name: str, value: Any, date_format: str = "%Y-%m-%d",
                  future_only: bool = False, past_only: bool = False) -> str:
    """
    Validate date string format.

    Args:
        name: Field name for error messages
        value: Date string to validate
        date_format: Expected date format (default: YYYY-MM-DD)
        future_only: If True, date must be in the future
        past_only: If True, date must be in the past

    Returns:
        Validated date string

    Raises:
        ValidationError: If date is invalid or doesn't meet constraints
    """
    if not isinstance(value, str):
        raise ValidationError(f"Field '{name}' must be a valid date", name)

    # Allow empty dates for optional fields
    if not value.strip():
        return value

    try:
        parsed_date = datetime.strptime(value.strip(), date_format)
    except ValueError:
        raise ValidationError(
            f"Field '{name}' must be in format {date_format}", name
        )

    # Check future/past constraints
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if future_only and parsed_date < today:
        raise ValidationError(
            f"Field '{name}' must be a future date", name
        )

    if past_only and parsed_date > today:
        raise ValidationError(
            f"Field '{name}' must be a past date", name
        )

    return value.strip()


def validate_product_id(value: Any) -> str:
    """
    Validate product ID format.

    Args:
        value: Product ID to validate

    Returns:
        Validated product ID

    Raises:
        ValidationError: If product ID is invalid
    """
    product_id = validate_string(
        "Product ID",
        value,
        min_length=1,
        max_length=50
    )
    return product_id


def validate_inventory_item(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all fields for an inventory item.

    Args:
        data: Dictionary containing inventory item data

    Returns:
        Dictionary with validated and normalized data

    Raises:
        ValidationError: If any validation fails
    """
    # Check required fields
    require_fields(data, ['id', 'name', 'category', 'stock', 'price', 'supplier'])

    validated = {}

    # Validate each field
    validated['id'] = validate_product_id(data['id'])
    validated['name'] = validate_string('Product Name', data['name'],
                                       min_length=1, max_length=100)
    validated['category'] = validate_string('Category', data['category'],
                                           min_length=1, max_length=50)
    validated['stock'] = parse_int('Stock', data['stock'], min_val=0)
    validated['price'] = parse_float('Price', data['price'], min_val=0.0, decimals=2)
    validated['supplier'] = validate_string('Supplier', data['supplier'],
                                           min_length=1, max_length=100)

    # Optional expiry date
    if 'expiry_date' in data and data['expiry_date']:
        validated['expiry_date'] = validate_date('Expiry Date', data['expiry_date'])
    else:
        validated['expiry_date'] = data.get('expiry_date', '')

    return validated


def validate_user_credentials(data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Validate user registration/login credentials.

    Args:
        data: Dictionary containing username and password

    Returns:
        Tuple of (username, password)

    Raises:
        ValidationError: If validation fails
    """
    require_fields(data, ['username', 'password'])

    username = validate_string('Username', data['username'],
                               min_length=3, max_length=50)

    # Password validation
    password = data['password']
    if not isinstance(password, str):
        raise ValidationError("Password must be a text value", "password")

    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long", "password")

    if len(password) > 200:
        raise ValidationError("Password must be at most 200 characters long", "password")

    return username, password


def sanitize_for_csv(value: Any) -> str:
    """
    Sanitize a value for safe CSV storage.

    Args:
        value: Value to sanitize

    Returns:
        Sanitized string value
    """
    if value is None:
        return ''

    # Convert to string and remove any problematic characters
    str_value = str(value).strip()

    # Remove or escape characters that could cause CSV injection
    # (formulas starting with =, +, -, @)
    if str_value and str_value[0] in ['=', '+', '-', '@']:
        str_value = "'" + str_value

    return str_value

