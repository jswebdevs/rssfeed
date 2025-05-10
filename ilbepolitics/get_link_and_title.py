import requests
from bs4 import BeautifulSoup
from log import log_step
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_links_and_titles(page_url, base_url, headers):
    log_step("WARNING: SSL certificate verification is disabled. This may expose you to security risks.")

    try:
        # Disabled SSL verification explicitly
        response = requests.get(page_url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()

        log_step(f"Raw HTML content for {page_url}: {response.text[:500]}...")

        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select('a.subject')

        log_step(f"Raw anchor tags for titles: {[str(a) for a in articles]}")

        results = []

        for a in articles:
            title = a.get_text(strip=True)
            relative_link = a.get('href', '')
            log_step(f"Found title: {title} with link: {relative_link}")

            parent = a.find_parent('li', class_='title')
            if parent:
                category_elements = parent.select('span.category a.lu-category')
                categories = [cat.get_text(strip=True) for cat in category_elements if cat.get_text(strip=True)]
            else:
                categories = []

            log_step(f"Categories for title '{title}': {categories}")

            if title and relative_link:
                full_link = urljoin(base_url, relative_link)
                if '#' in full_link:
                    full_link = full_link.split('#')[0]

                results.append({
                    'title': title,
                    'link': full_link,
                    'categories': categories
                })

        log_step(f"Found {len(results)} posts on {page_url}")
        return results

    except Exception as e:
        log_step(f"Error fetching {page_url}: {str(e)}")
        return []
