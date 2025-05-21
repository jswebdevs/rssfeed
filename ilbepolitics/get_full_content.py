from bs4 import BeautifulSoup, Comment
from log import log_step
from playwright.sync_api import sync_playwright
import requests

def get_full_content(post_url, headers):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(extra_http_headers=headers)
            page = context.new_page()

            page.goto(post_url, timeout=10000)
            page.wait_for_selector('.post-content', timeout=5000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'lxml')
        content_root = soup.find('div', class_='post-content')
        if not content_root:
            log_step(f"No .post-content found at {post_url}")
            return '', ''

        # Remove comments
        for comment in content_root.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Fix URLs in <img> and <video>
        image_urls = []
        video_urls = []
        for tag in content_root.find_all(['img', 'video']):
            if tag.name == 'img':
                src = tag.get('src', '')
                if src and not src.startswith('http'):
                    src = 'https://ncache.ilbe.com' + src if src.startswith('/files/attach') else 'https://ncache.ilbe.com/files/attach' + src
                tag['src'] = src
                tag['width'] = '720px'
                image_urls.append(src)

            if tag.name == 'video':
                src = tag.get('src', '')
                poster = tag.get('poster', '')

                if src and not src.startswith('http'):
                    src = 'https://ncache.ilbe.com' + src if src.startswith('/files/attach') else 'https://ncache.ilbe.com/files/attach' + src
                if poster and not poster.startswith('http'):
                    poster = 'https://ncache.ilbe.com' + poster if poster.startswith('/files/attach') else 'https://ncache.ilbe.com/files/attach' + poster

                tag['src'] = src
                tag['poster'] = poster
                tag['width'] = '720px'
                if 'controls' not in tag.attrs:
                    tag['controls'] = ''
                video_urls.append(src)

        cleaned_html = str(content_root)

        # Pick featured image
        featured_image = image_urls[0] if image_urls else None
        if featured_image:
            try:
                response = requests.head(featured_image, headers=headers, timeout=5)
                if response.status_code != 200:
                    featured_image = None
            except Exception as e:
                log_step(f"Failed to verify featured image {featured_image}: {str(e)}")
                featured_image = None

        log_step(
            f"==============\n"
            f"title: {soup.title.text.strip() if soup.title else 'N/A'}\n"
            f"link: {post_url}\n"
            f"content: {cleaned_html[:500]}{'...' if len(cleaned_html) > 500 else ''}\n"
            f"length: {len(cleaned_html)}\n"
            f"Featured Image: {featured_image}\n"
            f"Image URLs: {image_urls}\n"
            f"Video URLs: {video_urls}\n"
            f"=============="
        )

        return cleaned_html, featured_image

    except Exception as e:
        log_step(f"Error fetching content from {post_url}: {str(e)}")
        return '', ''
