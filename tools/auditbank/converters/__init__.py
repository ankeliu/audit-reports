"""Firm-specific converters: published report (page or PDF) -> standard report dict."""

from .halborn import HalbornConverter
from .runtime_verification import RuntimeVerificationConverter
from .veridise import VeridiseConverter

CONVERTERS = {"hal": HalbornConverter, "rv": RuntimeVerificationConverter, "ver": VeridiseConverter}
