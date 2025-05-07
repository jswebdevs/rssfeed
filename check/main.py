# main.py

from get_link_and_title import get_links_and_titles
from get_full_content import get_full_content
from feed_generation import generate_rss_feed
from log import log_step

BASE_URL = "https://ggoorr.net"
TARGET_URL = BASE_URL + "/main/page/{page_number}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36"
}
START_PAGE = 1
END_PAGE = 1

def main():
    all_posts = []

    for page_num in range(START_PAGE, END_PAGE + 1):
        url = TARGET_URL.format(page_number=page_num)
        log_step(f"Scraping page {page_num}: {url}")
        posts = get_links_and_titles(url, BASE_URL, HEADERS)

        for post in posts:
            content, featured_image = get_full_content(post['link'], HEADERS)
            post['content'] = content
            post['featured_image'] = featured_image
            log_step(f"Added content for: {post['title']} (length: {len(content)})")

        all_posts.extend(posts)

    log_step(f"Total posts collected: {len(all_posts)}")
    generate_rss_feed(all_posts)

if __name__ == "__main__":
    main()
