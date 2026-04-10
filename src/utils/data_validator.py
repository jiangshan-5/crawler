from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Utilities for validating and cleaning crawled data."""
    @staticmethod
    def validate_url(url):
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False

    @staticmethod
    def clean_text(text):
        if not text:
            return ""
        # Remove extra whitespaces and normalize
        return " ".join(text.split()).strip()
