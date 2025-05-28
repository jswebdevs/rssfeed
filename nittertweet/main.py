from get_link_and_title import get_links_and_titles
from get_full_content import get_full_content
from feed_generation import generate_rss_feed
from log import log_step
from bs4 import BeautifulSoup

import urllib.parse

BASE_URL = "https://nitter.net"
TARGET_URL = BASE_URL + "/elonmusk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}

MAX_PAGES = 5  # Optional limit to avoid infinite loops

def extract_next_cursor(soup):
    """Extract next cursor for 'Load more'."""
    more_button = soup.select_one("div.show-more a")
    if more_button and "href" in more_button.attrs:
        href = more_button['href']
        parsed = urllib.parse.urlparse(href)
        qs = urllib.parse.parse_qs(parsed.query)
        return qs.get('cursor', [None])[0]
    return None

def main():
    all_posts = []
    cursor = None
    page_count = 0

    while page_count < MAX_PAGES:
        current_url = TARGET_URL
        if cursor:
            current_url += f"?cursor={cursor}"

        log_step(f"Scraping page {page_count + 1}: {current_url}")
        try:
            posts, soup = get_links_and_titles(current_url, BASE_URL, HEADERS)
        except Exception as e:
            log_step(f"Failed to scrape: {str(e)}")
            break

        for post in posts:
            try:
                content, featured_image = get_full_content(post['link'], HEADERS)
                if not post.get('title') or not post.get('link'):
                    log_step(f"Skipping invalid post: {post}")
                    continue
                post['content'] = content
                post['featured_image'] = featured_image
                post['categories'] = post.get('categories', [])
                post['link'] = post['link'].replace('/main/', '/thisthat/').replace('/page/1', '')
                log_step(f"Added content: {post['title']}")
                all_posts.append(post)
            except Exception as e:
                log_step(f"Failed post: {post.get('title', 'unknown')}, {str(e)}")

        cursor = extract_next_cursor(soup)
        if not cursor:
            log_step("No more 'Load more' button found.")
            break

        page_count += 1

    log_step(f"Total posts collected: {len(all_posts)}")

    if all_posts:
        generate_rss_feed(all_posts)
    else:
        log_step("No posts to generate RSS feed")

if __name__ == "__main__":
    main()
