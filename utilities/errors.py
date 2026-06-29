# utilities/errors.py
"""
User-friendly error handling for MA-Grader.

Converts technical exceptions into instructor-friendly messages
with context about which student, what went wrong, and what to do.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ErrorCategory(Enum):
    """Error severity categories."""
    BLOCKING = "blocking"       # Can't continue (bad ZIP, missing template)
    STUDENT_ISSUE = "student"   # One student's file has a problem
    RECOVERABLE = "info"        # Handled automatically, FYI only


@dataclass
class GradingError:
    """
    Structured error with user-friendly message.
    
    Attributes:
        category: Severity level (blocking/student/info)
        student_name: Which student this affects (if applicable)
        problem: Plain English description of what went wrong
        action: What the instructor should do
        technical: Original technical error (for logs)
    """
    category: ErrorCategory
    problem: str
    action: str
    student_name: Optional[str] = None
    technical: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "category": self.category.value,
            "student_name": self.student_name,
            "problem": self.problem,
            "action": self.action,
            "technical": self.technical
        }
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        if self.student_name:
            return f"{self.student_name}: {self.problem}"
        return self.problem


@dataclass
class GradingResult:
    """
    Tracks grading results and issues for a batch.
    
    Use this to collect all issues during grading, then
    generate a summary at the end.
    """
    success_count: int = 0
    issues: list = field(default_factory=list)
    
    def add_success(self):
        """Record a successful grading."""
        self.success_count += 1
    
    def add_issue(self, error: GradingError):
        """Record an issue."""
        self.issues.append(error)
    
    def has_blocking_errors(self) -> bool:
        """Check if any blocking errors occurred."""
        return any(e.category == ErrorCategory.BLOCKING for e in self.issues)
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate a summary dict for the frontend."""
        student_issues = [e for e in self.issues if e.category == ErrorCategory.STUDENT_ISSUE]
        blocking = [e for e in self.issues if e.category == ErrorCategory.BLOCKING]
        info = [e for e in self.issues if e.category == ErrorCategory.RECOVERABLE]
        
        return {
            "success_count": self.success_count,
            "issue_count": len(self.issues),
            "student_issues": [e.to_dict() for e in student_issues],
            "blocking_errors": [e.to_dict() for e in blocking],
            "info_messages": [e.to_dict() for e in info]
        }


# ============================================================
# ERROR MESSAGE MAPPINGS
# ============================================================

def parse_file_not_found(error: Exception, student_name: Optional[str] = None) -> GradingError:
    """Parse FileNotFoundError into user-friendly message."""
    msg = str(error).lower()
    
    if "submission" in msg:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Missing submission file",
            action="Check if student submitted an .xlsx file (not .xls or .numbers)",
            technical=str(error)
        )
    elif "template" in msg or "grading sheet" in msg:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            problem="Grading template not found",
            action="Re-download the grading template or check the templates folder",
            technical=str(error)
        )
    elif "workspace" in msg or "output" in msg:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            problem="Workspace folder not found",
            action="Check that the workspace path exists and is accessible",
            technical=str(error)
        )
    else:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            student_name=student_name,
            problem="Required file not found",
            action="Check the file path and try again",
            technical=str(error)
        )


def parse_key_error(error: Exception, student_name: Optional[str] = None) -> GradingError:
    """Parse KeyError (usually missing Excel sheet/tab)."""
    msg = str(error)
    
    if "grading sheet" in msg.lower():
        return GradingError(
            category=ErrorCategory.BLOCKING,
            problem="Grading template is missing the 'Grading Sheet' tab",
            action="Re-download the grading template from the course materials",
            technical=str(error)
        )
    elif "income" in msg.lower():
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Missing 'Income Analysis' sheet",
            action="Student may have renamed or deleted required sheet",
            technical=str(error)
        )
    elif "unit" in msg.lower():
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Missing 'Unit Conversions' sheet",
            action="Student may have renamed or deleted required sheet",
            technical=str(error)
        )
    elif "currency" in msg.lower():
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Missing 'Currency Conversion' sheet",
            action="Student may have renamed or deleted required sheet",
            technical=str(error)
        )
    else:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem=f"Missing required sheet or data: {msg}",
            action="Check if student's file has all required sheets",
            technical=str(error)
        )


def parse_zip_error(error: Exception) -> GradingError:
    """Parse ZIP-related errors."""
    msg = str(error).lower()
    
    if "not a zip" in msg or "bad zip" in msg:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            problem="The uploaded file isn't a valid ZIP archive",
            action="Make sure you downloaded the submissions correctly from Canvas (should be a .zip file)",
            technical=str(error)
        )
    elif "path traversal" in msg or "security" in msg:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            problem="ZIP file contains suspicious paths (possible security issue)",
            action="Re-download the submissions from Canvas. If this persists, contact support.",
            technical=str(error)
        )
    else:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            problem="Error extracting ZIP file",
            action="The ZIP may be corrupted. Try re-downloading from Canvas.",
            technical=str(error)
        )


def parse_encoding_error(error: Exception, student_name: Optional[str] = None) -> GradingError:
    """Parse encoding/Unicode errors."""
    return GradingError(
        category=ErrorCategory.STUDENT_ISSUE,
        student_name=student_name,
        problem="File contains special characters that couldn't be processed",
        action="Student may have used emoji or non-English characters. Check their file manually.",
        technical=str(error)
    )


def parse_value_error(error: Exception, student_name: Optional[str] = None) -> GradingError:
    """Parse ValueError (usually data format issues)."""
    msg = str(error).lower()
    
    if "empty" in msg or "no data" in msg:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Required cells are empty",
            action="Student left required formula cells blank",
            technical=str(error)
        )
    else:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Invalid data format in submission",
            action="Check student's file for incorrectly formatted data",
            technical=str(error)
        )


def parse_permission_error(error: Exception, student_name: Optional[str] = None) -> GradingError:
    """Parse permission/access errors."""
    msg = str(error).lower()
    
    if "password" in msg or "protected" in msg or "encrypted" in msg:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="File is password-protected or encrypted",
            action="Ask student to resubmit without password protection",
            technical=str(error)
        )
    else:
        return GradingError(
            category=ErrorCategory.BLOCKING,
            student_name=student_name,
            problem="Cannot access file (permission denied)",
            action="Check if the file is open in another program, or try running as administrator",
            technical=str(error)
        )


def parse_excel_error(error: Exception, student_name: Optional[str] = None) -> GradingError:
    """Parse openpyxl/Excel-specific errors."""
    msg = str(error).lower()
    
    if "corrupt" in msg or "invalid" in msg:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Excel file appears to be corrupted",
            action="Ask student to resubmit. They may need to copy content to a new workbook.",
            technical=str(error)
        )
    elif "xls" in msg and "xlsx" not in msg:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="File is in old Excel format (.xls instead of .xlsx)",
            action="Ask student to save as .xlsx format and resubmit",
            technical=str(error)
        )
    else:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE,
            student_name=student_name,
            problem="Error reading Excel file",
            action="File may be corrupted or in an unsupported format",
            technical=str(error)
        )


def classify_error(
    error: Exception,
    student_name: Optional[str] = None,
    context: Optional[str] = None
) -> GradingError:
    """
    Main entry point: classify any exception into a user-friendly GradingError.
    
    Args:
        error: The exception that was raised
        student_name: Name of student whose file caused the error (if known)
        context: Additional context about where the error occurred
        
    Returns:
        GradingError with user-friendly message
    """
    error_type = type(error).__name__
    
    # Route to specific parsers based on error type
    if isinstance(error, FileNotFoundError):
        return parse_file_not_found(error, student_name)
    
    elif isinstance(error, KeyError):
        return parse_key_error(error, student_name)
    
    elif error_type in ('BadZipFile', 'BadZipfile', 'LargeZipFile'):
        return parse_zip_error(error)
    
    elif isinstance(error, (UnicodeDecodeError, UnicodeEncodeError)):
        return parse_encoding_error(error, student_name)
    
    elif isinstance(error, ValueError):
        result = parse_value_error(error, student_name)
        # Check for ZIP security errors (raised as ValueError)
        if "path traversal" in str(error).lower():
            return parse_zip_error(error)
        return result
    
    elif isinstance(error, PermissionError):
        return parse_permission_error(error, student_name)
    
    # Check for openpyxl errors by message content
    elif "corrupt" in str(error).lower() or "invalid file" in str(error).lower():
        return parse_excel_error(error, student_name)
    
    # Generic fallback
    else:
        return GradingError(
            category=ErrorCategory.STUDENT_ISSUE if student_name else ErrorCategory.BLOCKING,
            student_name=student_name,
            problem=f"Unexpected error: {error_type}",
            action="Check the technical details in logs or contact support",
            technical=str(error)
        )


def format_error_summary(result: GradingResult) -> str:
    """
    Format a human-readable summary of grading results.
    
    Args:
        result: GradingResult with all issues collected
        
    Returns:
        Multi-line string summary
    """
    lines = []
    
    # Header
    lines.append(f"✅ {result.success_count} students graded successfully")
    
    if result.issues:
        student_issues = [e for e in result.issues if e.category == ErrorCategory.STUDENT_ISSUE]
        blocking = [e for e in result.issues if e.category == ErrorCategory.BLOCKING]
        
        if blocking:
            lines.append(f"\n❌ {len(blocking)} blocking error(s):")
            for err in blocking:
                lines.append(f"   • {err.problem}")
                lines.append(f"     → {err.action}")
        
        if student_issues:
            lines.append(f"\n⚠️ {len(student_issues)} student issue(s):")
            for err in student_issues:
                name = err.student_name or "Unknown"
                lines.append(f"   • {name}: {err.problem}")
    
    return "\n".join(lines)
