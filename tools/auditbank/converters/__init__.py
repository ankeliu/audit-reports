"""Firm-specific converters: published report (page or PDF) -> standard report dict."""

from .halborn import HalbornConverter

CONVERTERS = {"hal": HalbornConverter}
