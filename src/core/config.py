import os

class RetryConfig:
    """Standard retry policy for all crawler requests."""
    MAX_RETRIES = 3
    RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
    BACKOFF_FACTOR = 2
    INITIAL_BACKOFF = 1

# Default paths
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), 'data', 'crawled_data')
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
