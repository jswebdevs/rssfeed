import time
from get_link_and_title import get_links_and_titles
from get_full_content import get_full_content
from feed_generation import generate_rss_feed
from log import log_step
from urllib.parse import urljoin

BASE_URL = "https://nitter.net"
TARGET_USER = "elonmusk"
START_URL = f"{BASE_URL}/{TARGET_USER}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}

MAX_PAGES = 5  # Adjust based on how many pages you want to scrape

def extract_next_cursor(soup):
    if soup is None:
        return None
    more_button = soup.select_one("div.show-more a")
    if more_button and more_button.has_attr("href"):
        return more_button["href"]
    return None

def main():
    all_posts = []
    page_count = 0
    cursor = ""

    while page_count < MAX_PAGES:
        current_url = START_URL + cursor
        log_step(f"Scraping page {page_count + 1}: {current_url}")

        retry_count = 0
        while retry_count < 3:
            posts, soup = get_links_and_titles(current_url, BASE_URL, HEADERS)
            if soup is None:
                log_step("Hit rate limit or fetch failed. Retrying...")
                time.sleep(5 * (retry_count + 1))  # Exponential backoff
                retry_count += 1
                continue
            break
        else:
            log_step("Failed to retrieve page after multiple retries.")
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

                log_step(f"Added content for: {post['title']} (link: {post['link']}, content length: {len(content)}, categories: {post['categories']})")
                all_posts.append(post)

            except Exception as e:
                log_step(f"Failed to process post {post.get('title', 'unknown')}: {str(e)}")
                continue

        page_count += 1
        cursor_path = extract_next_cursor(soup)
        if not cursor_path:
            log_step("No more pages to load.")
            break
        cursor = cursor_path  # e.g., "?cursor=XYZ"

    log_step(f"Total posts collected: {len(all_posts)}")

    if all_posts:
        generate_rss_feed(all_posts)
    else:
        log_step("No posts to generate RSS feed")

if __name__ == "__main__":
    main()
