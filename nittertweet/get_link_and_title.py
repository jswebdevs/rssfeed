import requests
from bs4 import BeautifulSoup
from log import log_step
from urllib.parse import urljoin

def get_links_and_titles(page_url, base_url, headers):
    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        results = []

        # Each tweet is within a <div class="timeline-item">
        timeline_items = soup.select('div.timeline-item')

        for item in timeline_items:
            # Get tweet content (title)
            content_div = item.select_one('div.tweet-content')
            title = content_div.get_text(strip=True) if content_div else None

            # Get link to the tweet
            link_elem = item.select_one('a.tweet-link')
            relative_link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else None

            # Skip if either title or link is missing
            if not title or not relative_link:
                log_step(f"Skipping incomplete item: title='{title}', link='{relative_link}'")
                continue

            # Build the absolute link
            full_link = urljoin(base_url, relative_link.split('#')[0])  # remove # fragments

            # Nitter does not use categories; empty list
            categories = []

            results.append({
                'title': title,
                'link': full_link,
                'categories': categories
            })

            log_step(f"Found tweet: '{title}' at {full_link}")

        log_step(f"Found {len(results)} posts on {page_url}")
        return results, soup

    except Exception as e:
        log_step(f"Error fetching {page_url}: {str(e)}")
        return [], None
