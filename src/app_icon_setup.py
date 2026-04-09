import os
import sys
import time
import requests
from PIL import Image
from io import BytesIO

# Add src to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from universal_crawler_v2 import UniversalCrawlerV2

def setup_app_icons():
    # Target icons and their search keywords
    icon_map = {
        'dashboard': 'dashboard',
        'config': 'settings',
        'history': 'history',
        'logs': 'terminal',
        'lang': 'world',
        'add': 'plus',
        'del': 'delete',
        'logo': 'spider'
    }

    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets'))
    os.makedirs(assets_dir, exist_ok=True)
    
    print(f"--- Starting Icon Harvest ---")
    print(f"Target Directory: {assets_dir}\n")

    # Initialize crawler in Advanced Mode (Headed for Flaticon)
    # Using a dummy URL first, but we will pass is_flaticon_task=True
    crawler = UniversalCrawlerV2(
        base_url="https://www.flaticon.com/",
        use_advanced_mode=True,
        is_flaticon_task=True
    )

    try:
        if not crawler.advanced_crawler:
            print("Failed to initialize Advanced Crawler. Is Chrome installed?")
            return

        for name, keyword in icon_map.items():
            search_url = f"https://www.flaticon.com/free-icons/{keyword}"
            print(f"Fetching icon for: {keyword}...")
            
            # Use Advanced mode to bypass Cloudflare
            soup = crawler.advanced_crawler.fetch_page(search_url, wait_time=2.5, timeout=20)
            
            if not soup:
                print(f"  [!] Failed to load page for {keyword}")
                continue

            # Find icon candidates (Flaticon structure)
            # We want the first icon in the list
            img_tag = soup.select_one('.icon--item img') or soup.select_one('li.icon--item img')
            
            if not img_tag:
                print(f"  [!] No icons found for {keyword}")
                continue

            img_url = img_tag.get('src') or img_tag.get('data-src')
            if not img_url:
                print(f"  [!] Could not extract image URL for {keyword}")
                continue

            print(f"  [+] Found icon: {img_url}")
            
            # Download Image
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.flaticon.com/'
                }
                resp = requests.get(img_url, headers=headers, timeout=15)
                resp.raise_for_status()
                
                # Process and Resize
                img = Image.open(BytesIO(resp.content))
                
                # Save as PNG
                save_path = os.path.join(assets_dir, f"{name}.png")
                # Ensure it's RGBA for transparency
                img.convert("RGBA").save(save_path, "PNG")
                
                print(f"  [*] Saved to: {save_path}")
                
            except Exception as e:
                print(f"  [!] Download/Process failed for {keyword}: {e}")
            
            time.sleep(1.5) # Courtesy delay

    finally:
        crawler.close()
        print("\n--- Icon Harvest Complete ---")

if __name__ == "__main__":
    setup_app_icons()
