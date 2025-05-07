import requests
from bs4 import BeautifulSoup
from log import log_step
from urllib.parse import urljoin

def get_links_and_titles(page_url, base_url, headers):
    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Log the entire raw HTML response to understand what's being returned
        log_step(f"Raw HTML content for {page_url}: {response.text[:500]}...")  # Log the first 500 characters for inspection

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Select the anchor tags that hold the titles
        articles = soup.select('a.lu-title')
        
        # Log the exact raw HTML of the anchor tags
        log_step(f"Raw anchor tags for titles: {[str(a) for a in articles]}")

        results = []

        for a in articles:
            title = a.get_text(strip=False)  # Make sure no whitespace is stripped accidentally
            relative_link = a.get('href', '')

            # Log the title and link to ensure we're capturing the full title and link
            log_step(f"Found title: {title} with link: {relative_link}")

            if title and relative_link:
                # Build the absolute link
                full_link = urljoin(base_url, relative_link)

                # Remove any fragment (like #comment_...)
                if '#' in full_link:
                    full_link = full_link.split('#')[0]

                results.append({'title': title, 'link': full_link})

        log_step(f"Found {len(results)} posts on {page_url}")
        return results

    except Exception as e:
        log_step(f"Error fetching {page_url}: {str(e)}")
        return []
