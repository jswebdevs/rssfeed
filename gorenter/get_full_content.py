import requests
from bs4 import BeautifulSoup, Comment
from log import log_step

def get_full_content(post_url, headers):
    try:
        response = requests.get(post_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_root = soup.find('div', class_='xe_content')
        if not content_root:
            log_step(f"Content container not found: {post_url}")
            return '', ''

        log_step(f"Raw content HTML: {str(content_root)[:500]}{'...' if len(str(content_root)) > 500 else ''}")

        for comment in content_root.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        elements = []
        image_urls = []
        video_urls = []

        for tag in content_root.descendants:
            if isinstance(tag, str):
                continue

            if tag.name == 'img':
                src = tag.get('src', '')
                if not src.startswith('http'):
                    if src.startswith('/files/attach'):
                        src = 'https://cdn.ggoorr.net' + src
                    else:
                        src = 'https://cdn.ggoorr.net/files/attach' + src
                tag['src'] = src
                tag['width'] = '720px'

                image_urls.append(src)
                tag_str = str(tag)
                elements.append(f'<p>{tag_str}</p>')

            elif tag.name == 'video':
                src = tag.get('src', '')
                poster = tag.get('poster', '')

                if not src:
                    continue

                if not src.startswith('http'):
                    if src.startswith('/files/attach'):
                        src = 'https://cdn.ggoorr.net' + src
                    else:
                        src = 'https://cdn.ggoorr.net/files/attach' + src
                if poster and not poster.startswith('http'):
                    if poster.startswith('/files/attach'):
                        poster = 'https://cdn.ggoorr.net' + poster
                    else:
                        poster = 'https://cdn.ggoorr.net/files/attach' + poster

                tag['src'] = src
                tag['poster'] = poster
                tag['controls'] = 'controls'
                tag['width'] = '720px'

                video_urls.append(src)
                tag_str = str(tag)
                elements.append(f'<p>{tag_str}</p>')

            elif tag.name == 'source':
                parent_video = tag.find_parent('video')
                if parent_video:
                    src = tag.get('src', '')
                    if src and not src.startswith('http'):
                        if src.startswith('/files/attach'):
                            src = 'https://cdn.ggoorr.net' + src
                        else:
                            src = 'https://cdn.ggoorr.net/files/attach' + src
                        tag['src'] = src

        cleaned_html = ''.join(elements)

        log_step(f"Video URLs for post {post_url}: {video_urls}")

        featured_image = None
        if image_urls:
            featured_image = image_urls[0]
            try:
                img_response = requests.head(featured_image, headers=headers, timeout=5)
                log_step(f"Featured image {featured_image} status: {img_response.status_code}")
                if img_response.status_code != 200:
                    featured_image = None
            except Exception as e:
                log_step(f"Error validating featured image {featured_image}: {str(e)}")
                featured_image = None

        if not featured_image and content_root.find('video'):
            poster = content_root.find('video').get('poster', '')
            if poster:
                if not poster.startswith('http'):
                    if poster.startswith('/files/attach'):
                        poster = 'https://cdn.ggoorr.net' + poster
                    else:
                        poster = 'https://cdn.ggoorr.net/files/attach' + poster
                try:
                    poster_response = requests.head(poster, headers=headers, timeout=5)
                    log_step(f"Featured image (poster) {poster} status: {poster_response.status_code}")
                    if poster_response.status_code == 200:
                        featured_image = poster
                except Exception as e:
                    log_step(f"Error validating featured image (poster) {poster}: {str(e)}")

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
