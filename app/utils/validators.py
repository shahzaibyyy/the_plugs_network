"""
Data validation utilities for enterprise applications.
"""
import re
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException


class ValidationError(Exception):
    """Custom validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class EmailValidator:
    """Email validation utilities."""
    
    @staticmethod
    def validate(email: str) -> str:
        """
        Validate email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            str: Normalized email address
            
        Raises:
            ValidationError: If email is invalid
        """
        try:
            validation = validate_email(email)
            return validation.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {str(e)}", "email")
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """
        Check if email address is valid.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            EmailValidator.validate(email)
            return True
        except ValidationError:
            return False


class PhoneValidator:
    """Phone number validation utilities."""
    
    @staticmethod
    def validate(phone: str, region: str = "US") -> str:
        """
        Validate and format phone number.
        
        Args:
            phone: Phone number to validate
            region: Default region code
            
        Returns:
            str: Formatted phone number in E164 format
            
        Raises:
            ValidationError: If phone number is invalid
        """
        try:
            parsed = phonenumbers.parse(phone, region)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number", "phone")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException as e:
            raise ValidationError(f"Invalid phone number: {str(e)}", "phone")
    
    @staticmethod
    def is_valid(phone: str, region: str = "US") -> bool:
        """
        Check if phone number is valid.
        
        Args:
            phone: Phone number to check
            region: Default region code
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            PhoneValidator.validate(phone, region)
            return True
        except ValidationError:
            return False


class PasswordValidator:
    """Password validation utilities."""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    
    @staticmethod
    def validate(password: str, min_length: int = MIN_LENGTH) -> None:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            min_length: Minimum password length
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if len(password) < min_length:
            raise ValidationError(
                f"Password must be at least {min_length} characters long",
                "password"
            )
        
        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValidationError(
                f"Password must be no more than {PasswordValidator.MAX_LENGTH} characters long",
                "password"
            )
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                "Password must contain at least one uppercase letter",
                "password"
            )
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                "Password must contain at least one lowercase letter",
                "password"
            )
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError(
                "Password must contain at least one digit",
                "password"
            )
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password must contain at least one special character",
                "password"
            )
    
    @staticmethod
    def is_valid(password: str, min_length: int = MIN_LENGTH) -> bool:
        """
        Check if password meets requirements.
        
        Args:
            password: Password to check
            min_length: Minimum password length
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            PasswordValidator.validate(password, min_length)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def get_strength_score(password: str) -> int:
        """
        Get password strength score (0-100).
        
        Args:
            password: Password to evaluate
            
        Returns:
            int: Strength score from 0-100
        """
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15
        
        # Complexity bonuses
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:
            score += 15
        
        return min(score, 100)


class URLValidator:
    """URL validation utilities."""
    
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    @staticmethod
    def validate(url: str) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            str: Validated URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not URLValidator.URL_PATTERN.match(url):
            raise ValidationError("Invalid URL format", "url")
        return url
    
    @staticmethod
    def is_valid(url: str) -> bool:
        """
        Check if URL is valid.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            URLValidator.validate(url)
            return True
        except ValidationError:
            return False


class UUIDValidator:
    """UUID validation utilities."""
    
    @staticmethod
    def validate(value: Union[str, uuid.UUID]) -> uuid.UUID:
        """
        Validate UUID format.
        
        Args:
            value: UUID to validate
            
        Returns:
            uuid.UUID: Validated UUID object
            
        Raises:
            ValidationError: If UUID is invalid
        """
        try:
            if isinstance(value, str):
                return uuid.UUID(value)
            elif isinstance(value, uuid.UUID):
                return value
            else:
                raise ValidationError("Invalid UUID type", "uuid")
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid UUID format: {str(e)}", "uuid")
    
    @staticmethod
    def is_valid(value: Union[str, uuid.UUID]) -> bool:
        """
        Check if UUID is valid.
        
        Args:
            value: UUID to check
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            UUIDValidator.validate(value)
            return True
        except ValidationError:
            return False


class DateTimeValidator:
    """Date and time validation utilities."""
    
    @staticmethod
    def validate_date(date_str: str, format: str = "%Y-%m-%d") -> date:
        """
        Validate date string.
        
        Args:
            date_str: Date string to validate
            format: Expected date format
            
        Returns:
            date: Validated date object
            
        Raises:
            ValidationError: If date is invalid
        """
        try:
            return datetime.strptime(date_str, format).date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {str(e)}", "date")
    
    @staticmethod
    def validate_datetime(datetime_str: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """
        Validate datetime string.
        
        Args:
            datetime_str: Datetime string to validate
            format: Expected datetime format
            
        Returns:
            datetime: Validated datetime object
            
        Raises:
            ValidationError: If datetime is invalid
        """
        try:
            return datetime.strptime(datetime_str, format)
        except ValueError as e:
            raise ValidationError(f"Invalid datetime format: {str(e)}", "datetime")
    
    @staticmethod
    def validate_iso_datetime(datetime_str: str) -> datetime:
        """
        Validate ISO format datetime string.
        
        Args:
            datetime_str: ISO datetime string to validate
            
        Returns:
            datetime: Validated datetime object
            
        Raises:
            ValidationError: If datetime is invalid
        """
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValidationError(f"Invalid ISO datetime format: {str(e)}", "datetime")


class DataValidator:
    """General data validation utilities."""
    
    @staticmethod
    def validate_length(
        value: str, 
        min_length: Optional[int] = None, 
        max_length: Optional[int] = None,
        field_name: str = "field"
    ) -> str:
        """
        Validate string length.
        
        Args:
            value: String to validate
            min_length: Minimum length
            max_length: Maximum length
            field_name: Field name for error messages
            
        Returns:
            str: Validated string
            
        Raises:
            ValidationError: If length is invalid
        """
        length = len(value)
        
        if min_length is not None and length < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters long",
                field_name
            )
        
        if max_length is not None and length > max_length:
            raise ValidationError(
                f"{field_name} must be no more than {max_length} characters long",
                field_name
            )
        
        return value
    
    @staticmethod
    def validate_range(
        value: Union[int, float], 
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str = "field"
    ) -> Union[int, float]:
        """
        Validate numeric range.
        
        Args:
            value: Number to validate
            min_value: Minimum value
            max_value: Maximum value
            field_name: Field name for error messages
            
        Returns:
            Union[int, float]: Validated number
            
        Raises:
            ValidationError: If value is out of range
        """
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field_name
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be no more than {max_value}",
                field_name
            )
        
        return value
    
    @staticmethod
    def validate_choices(
        value: Any, 
        choices: List[Any], 
        field_name: str = "field"
    ) -> Any:
        """
        Validate value is in allowed choices.
        
        Args:
            value: Value to validate
            choices: List of allowed choices
            field_name: Field name for error messages
            
        Returns:
            Any: Validated value
            
        Raises:
            ValidationError: If value not in choices
        """
        if value not in choices:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(map(str, choices))}",
                field_name
            )
        
        return value
    
    @staticmethod
    def validate_regex(
        value: str, 
        pattern: str, 
        field_name: str = "field",
        error_message: Optional[str] = None
    ) -> str:
        """
        Validate string matches regex pattern.
        
        Args:
            value: String to validate
            pattern: Regex pattern
            field_name: Field name for error messages
            error_message: Custom error message
            
        Returns:
            str: Validated string
            
        Raises:
            ValidationError: If string doesn't match pattern
        """
        if not re.match(pattern, value):
            message = error_message or f"{field_name} format is invalid"
            raise ValidationError(message, field_name)
        
        return value


# Convenience validation functions
def validate_email(email: str) -> str:
    """Validate email address."""
    return EmailValidator.validate(email)


def validate_phone(phone: str, region: str = "US") -> str:
    """Validate phone number."""
    return PhoneValidator.validate(phone, region)


def validate_password(password: str, min_length: int = 8) -> None:
    """Validate password strength."""
    PasswordValidator.validate(password, min_length)


def validate_url(url: str) -> str:
    """Validate URL format."""
    return URLValidator.validate(url)


def validate_uuid(value: Union[str, uuid.UUID]) -> uuid.UUID:
    """Validate UUID format."""
    return UUIDValidator.validate(value)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present and not empty.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing or empty
    """
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            raise ValidationError(f"{field} is required", field)
