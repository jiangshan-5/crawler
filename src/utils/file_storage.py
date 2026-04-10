import os
import re
import json
import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def sanitize_filename(name):
    """Sanitize a string to be a safe filename, preserving Chinese/Unicode characters."""
    if not name: return 'unnamed'
    # Only strip characters illegal on Windows filenames: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', '_', str(name).strip())
    cleaned = cleaned.strip(' ._')
    return cleaned[:120] or 'unnamed'

def save_to_json(data, output_dir, filename=None):
    if not filename:
        filename = f"crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filepath = os.path.join(output_dir, f'{filename}.json')
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f'saved json: {filepath}')
        return filepath
    except Exception as e:
        logger.error(f'save json failed: {e}')
        return None

def save_to_csv(data, output_dir, filename=None):
    if not data: return None
    if not filename:
        filename = f"crawled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    filepath = os.path.join(output_dir, f'{filename}.csv')
    try:
        os.makedirs(output_dir, exist_ok=True)
        # Handle both list of dicts and nested novel structures (simplified)
        rows = data if isinstance(data, list) else [data]
        if not rows or not isinstance(rows[0], dict): return None
        
        fieldnames = list(rows[0].keys())
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f'saved csv: {filepath}')
        return filepath
    except Exception as e:
        logger.error(f'save csv failed: {e}')
        return None
