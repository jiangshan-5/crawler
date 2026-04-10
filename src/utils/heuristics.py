import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def flaticon_v1_heuristic(soup, item_selectors):
    """
    Specific heuristic extraction for Flaticon.com when standard selectors fail.
    Based on anchor patterns observed on the site.
    """
    rows = []
    seen = set()
    # Flaticon free icons usually have specific href patterns
    anchors = soup.select('a[href*="/free-icon/"]')
    
    for anchor in anchors:
        href = (anchor.get('href') or '').strip()
        if not href:
            continue
        
        full_link = urljoin('https://www.flaticon.com', href)
        if full_link in seen:
            continue
        seen.add(full_link)

        image = ''
        title = ''
        img = anchor.select_one('img')
        if img:
            image = (img.get('src') or img.get('data-src') or '').strip()
            title = (img.get('alt') or '').strip()
        
        if not title:
            title = (anchor.get('title') or anchor.get_text(strip=True) or '').strip()

        row = {}
        for field_name in item_selectors.keys():
            # In a real engine, we'd use a field intent detector here
            # For simplicity in this heuristic, we map to the most likely fields
            fname_lower = field_name.lower()
            if any(t in fname_lower for t in ['link', 'url', 'href']):
                row[field_name] = full_link
            elif any(t in fname_lower for t in ['img', 'image', 'src']):
                row[field_name] = image
            else:
                row[field_name] = title

        if row and any(row.values()):
            rows.append(row)
            
    if rows:
        logger.info(f'[heuristics] Flaticon fallback extracted {len(rows)} items')
    return rows
