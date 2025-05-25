from bs4 import BeautifulSoup, Comment
from log import log_step
from playwright.sync_api import sync_playwright
import requests
import time

def get_full_content(post_url, headers):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(extra_http_headers=headers)
            page = context.new_page()

            start_time = time.time()
            page.goto(post_url, timeout=60000, wait_until="domcontentloaded")
            duration = time.time() - start_time
            log_step(f"[⏱️] Page loaded in {duration:.2f}s: {post_url}")

            page.wait_for_selector('.view_cont', timeout=10000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'lxml')
        content_root = soup.find('div', class_='view_cont')
        if not content_root:
            log_step(f"[⚠️] No .view_cont found at {post_url}")
            return '', ''
                # Remove ads and unrelated blocks
        ad_selectors = [
            'div.view_ad',       # top ad
            'div[id^="dcamp_ad"]',  # digitalcamp ads
            'div.mt_bn_box',     # bottom ad box
            'script',            # inline ad scripts
            'iframe',            # ad iframes
            'h2:has(span:contains("Related Articles"))',  # "Related Articles" section header
            'div.news_box.connect'  # Related articles list
        ]
        for selector in ad_selectors:
            for tag in content_root.select(selector):
                tag.decompose()

        # Remove HTML comments
        for comment in content_root.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        image_urls = []
        video_urls = []
        for tag in content_root.find_all(['img', 'video']):
            if tag.name == 'img':
                src = tag.get('src', '')
                if src and not src.startswith('http'):
                    src = 'https://edgio.clien.net' + src if src.startswith('F01') else 'https://edgio.clien.netF01' + src
                tag['src'] = src
                tag['width'] = '720px'
                image_urls.append(src)

            if tag.name == 'video':
                src = tag.get('src', '')
                poster = tag.get('poster', '')
                if src and not src.startswith('http'):
                    src = 'https://edgio.clien.net' + src if src.startswith('F01') else 'https://edgio.clien.netF01' + src
                if poster and not poster.startswith('http'):
                    poster = 'https://edgio.clien.net' + poster if poster.startswith('F01') else 'https://edgio.clien.netF01' + poster

                tag['src'] = src
                tag['poster'] = poster
                tag['width'] = '720px'
                if 'controls' not in tag.attrs:
                    tag['controls'] = ''
                video_urls.append(src)

        cleaned_html = str(content_root)

        # Verify featured image
        featured_image = image_urls[0] if image_urls else None
        if featured_image:
            try:
                response = requests.head(featured_image, headers=headers, timeout=5)
                if response.status_code != 200:
                    featured_image = None
            except Exception as e:
                log_step(f"[⚠️] Failed to verify featured image {featured_image}: {str(e)}")
                featured_image = None

        log_step(
            f"==============\n"
            f"[📰] Title: {soup.title.text.strip() if soup.title else 'N/A'}\n"
            f"[🔗] Link: {post_url}\n"
            f"[📄] Content: {cleaned_html[:500]}{'...' if len(cleaned_html) > 500 else ''}\n"
            f"[🔢] Length: {len(cleaned_html)} chars\n"
            f"[🖼️] Featured Image: {featured_image}\n"
            f"[🖼️] Image URLs: {image_urls}\n"
            f"[🎞️] Video URLs: {video_urls}\n"
            f"=============="
        )

        return cleaned_html, featured_image

    except Exception as e:
        log_step(f"[❌] Error fetching content from {post_url}: {str(e)}")
        return '', ''
