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
                    src = 'https://cdn.ggoorr.net/files/attach' + src if not src.startswith('/files/attach') else 'https://cdn.ggoorr.net' + src
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

                # Correct video src and poster paths
                if not src.startswith('http'):
                    src = 'https://cdn.ggoorr.net/files/attach' + src if not src.startswith('/files/attach') else 'https://cdn.ggoorr.net' + src
                if poster and not poster.startswith('http'):
                    poster = 'https://cdn.ggoorr.net/files/attach' + poster if not poster.startswith('/files/attach') else 'https://cdn.ggoorr.net' + poster

                tag.attrs = {
                    'src': src,
                    'poster': poster,
                    'controls': 'controls',
                    'width': tag.get('width', '560'),
                    'height': tag.get('height', '315')
                }
                video_urls.append(src)
                elements.append(f'<p>{str(tag)}</p>')  # Wrap video in p tag

        cleaned_html = ''.join(elements)

        # Log all video URLs
        log_step(f"Video URLs for post {post_url}: {video_urls}")

        # Select featured image
        featured_image = None
        if image_urls:
            featured_image = image_urls[0]
            # Validate image URL
            try:
                img_response = requests.head(featured_image, headers=headers, timeout=5)
                log_step(f"Featured image {featured_image} status: {img_response.status_code}")
                if img_response.status_code != 200:
                    log_step(f"Invalid featured image {featured_image}, status: {img_response.status_code}")
                    featured_image = None
            except Exception as e:
                log_step(f"Error validating featured image {featured_image}: {str(e)}")
                featured_image = None

        # If no image found, try using video poster
        if not featured_image and content_root.find('video'):
            poster = content_root.find('video').get('poster', '')
            if poster:
                if not poster.startswith('http'):
                    poster = 'https://cdn.ggoorr.net/files/attach' + poster if not poster.startswith('/files/attach') else 'https://cdn.ggoorr.net' + poster
                featured_image = poster
                try:
                    poster_response = requests.head(poster, headers=headers, timeout=5)
                    log_step(f"Featured image (poster) {featured_image} status: {poster_response.status_code}")
                    if poster_response.status_code != 200:
                        featured_image = None
                except Exception as e:
                    log_step(f"Error validating featured image (poster) {featured_image}: {str(e)}")
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
