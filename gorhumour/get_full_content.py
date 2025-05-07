import requests
from bs4 import BeautifulSoup, Comment
from log import log_step

def get_full_content(post_url, headers):
    try:
        response = requests.get(post_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_root = soup.find('div', class_='slatc-content')
        if not content_root:
            log_step(f"Content container not found: {post_url}")
            return '', ''

        # Log raw HTML of content_root
        log_step(f"Raw content HTML: {str(content_root)[:500]}{'...' if len(str(content_root)) > 500 else ''}")

        # Remove comments
        for comment in content_root.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        elements = []
        image_urls = []
        video_urls = []

        for tag in content_root.find_all(['p', 'img', 'video']):
            if tag.name == 'p' and not tag.get_text(strip=True):
                continue  # skip empty <p>

            if tag.name == 'img':
                src = tag.get('src', '')
                if not src.startswith('http'):
                    src = 'https://cdn.ggoorr.net' + src.replace('/files/attach', '')
                tag.attrs = {
                    'src': src,
                    'alt': tag.get('alt', ''),
                    'width': tag.get('width', ''),
                    'height': tag.get('height', '')
                }
                image_urls.append(src)
                elements.append(f'<p>{str(tag)}</p>')  # Wrap img in p tag

            elif tag.name == 'video':
                src = tag.get('src', '')
                poster = tag.get('poster', '')
                if not src:
                    log_step(f"Skipping video tag with no src: {str(tag)}")
                    continue
                if not src.startswith('http'):
                    src = 'https://cdn.ggoorr.net' + src.replace('/files/attach', '')
                if poster and not poster.startswith('http'):
                    poster = 'https://cdn.ggoorr.net' + poster.replace('/files/attach', '')
                tag.attrs = {
                    'src': src,
                    'poster': poster,
                    'controls': 'controls',
                    'width': tag.get('width', '560'),
                    'height': tag.get('height', '315')
                }
                video_urls.append(src)
                elements.append(f'<p>{str(tag)}</p>')  # Wrap video in p tag

        cleaned_html = ''.join(elements)  # Join without newlines for WordPress compatibility

        # Log all video URLs
        log_step(f"Video URLs for post {post_url}: {video_urls}")

        featured_image = image_urls[0] if image_urls else None
        if not featured_image and content_root.find('video'):
            poster = content_root.find('video').get('poster', '')
            if poster and not poster.startswith('http'):
                featured_image = 'https://cdn.ggoorr.net' + poster.replace('/files/attach', '')
            else:
                featured_image = poster

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