import requests
from bs4 import BeautifulSoup, Comment
from log import log_step

def get_full_content(post_url, headers, verify= False):
    try:
        response = requests.get(post_url, timeout=10)
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
                    if src.startswith('/F01'):
                        src = 'https://img-cdn.theqoo.net' + src
                    else:
                        src = 'https://img-cdn.theqoo.net/' + src
                tag['src'] = src
                if 'width' not in tag.attrs:
                    tag['width'] = '720px'

                image_urls.append(src)
                tag_str = str(tag)
                elements.append(f'<p>{tag_str}</p>')

            elif tag.name == 'video':
                src = tag.get('src', '')
                poster = tag.get('poster', '')

                if not src:
                    log_step(f"Skipping video tag with no src: {str(tag)}")
                    continue

                if not src.startswith('http'):
                    if src.startswith('/F01'):
                        src = 'https://img-cdn.theqoo.net' + src
                    else:
                        src = 'https://img-cdn.theqoo.net/' + src
                if poster and not poster.startswith('http'):
                    if poster.startswith('/F01'):
                        poster = 'https://img-cdn.theqoo.net' + poster
                    else:
                        poster = 'https://img-cdn.theqoo.net/' + poster

                video_attrs = tag.attrs.copy()
                video_attrs['src'] = src
                if poster:
                    video_attrs['poster'] = poster
                if 'controls' not in video_attrs:
                    video_attrs['controls'] = ''
                if 'width' not in video_attrs:
                    video_attrs['width'] = '720px'

                log_step(f"Video tag attributes for {post_url}: {video_attrs}")

                video_urls.append(src)

                attr_strings = []
                for k, v in video_attrs.items():
                    if v is None:
                        continue
                    elif v == '' or v is True:
                        attr_strings.append(k)
                    else:
                        attr_strings.append(f'{k}="{v}"')
                video_tag = f"<video {' '.join(attr_strings)}></video>"
                elements.append(f'<p>{video_tag}</p>')

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
                    if poster.startswith('/F01'):
                        poster = 'https://img-cdn.theqoo.net' + poster
                    else:
                        poster = 'https://img-cdn.theqoo.net/' + poster
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