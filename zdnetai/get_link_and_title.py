import requests
from bs4 import BeautifulSoup
from log import log_step
from urllib.parse import urljoin

def get_links_and_titles(page_url, base_url, headers, verify=False):
    try:
        response = requests.get(page_url, headers=headers, timeout=10, verify=verify)
        response.raise_for_status()

        log_step(f"Raw HTML content for {page_url}: {response.text[:500]}...")

        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.select('div.newsPost')
        log_step(f"Found {len(posts)} .newsPost blocks on the page")

        results = []

        for post in posts:
            thumb_link_tag = post.select_one('div.assetThumb > a')
            text_link_tag = post.select_one('div.assetText > a')
            title_tag = text_link_tag.select_one('h3') if text_link_tag else None

            if not thumb_link_tag or not title_tag:
                log_step("Skipping one post due to missing thumbnail <a> or <h3> tag")
                continue

            relative_link = thumb_link_tag.get('href', '') or text_link_tag.get('href', '')
            title = title_tag.get_text(strip=True)

            log_step(f"Found title: {title} with link: {relative_link}")

            full_link = urljoin(base_url, relative_link)
            if '#' in full_link:
                full_link = full_link.split('#')[0]

            results.append({
                'title': title,
                'link': full_link,
                'categories': []
            })

        log_step(f"Found {len(results)} valid posts on {page_url}")
        return results

    except Exception as e:
        log_step(f"Error fetching {page_url}: {str(e)}")
        return []
