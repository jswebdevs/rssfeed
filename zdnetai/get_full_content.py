import requests
from bs4 import BeautifulSoup, Comment
from log import log_step

def get_full_content(post_url, headers, verify=False):
    try:
        response = requests.get(post_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Updated to the correct article body container
        article_body = soup.find('div', id='articleBody')
        if not article_body:
            log_step(f"Content container not found: {post_url}")
            return '', ''

        content_root = article_body.find('div', style=lambda x: x and 'font-size' in x)
        if not content_root:
            log_step(f"Content sub-container not found: {post_url}")
            return '', ''

        # Remove all ad-related divs
        for ad_class in ['view_ad', 'mt_bn_box', 'iwmads']:
            for ad_div in content_root.find_all('div', class_=ad_class):
                ad_div.decompose()

        # Remove HTML comments
        for comment in content_root.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        elements = []
        image_urls = []
        video_urls = []

        for tag in content_root.descendants:
            if isinstance(tag, str):
                continue

            # Handle image tags
            if tag.name == 'img':
                src = tag.get('src', '')
                if not src.startswith('http'):
                    if src.startswith('/F01') or src.startswith('//'):
                        src = 'https:' + src
                    else:
                        src = 'https://zdnet.co.kr' + src  # fallback base

                tag['src'] = src
                tag['width'] = '720px'
                image_urls.append(src)
                elements.append(f'<p>{str(tag)}</p>')

            # Handle video tags
            elif tag.name == 'video':
                src = tag.get('src', '')
                poster = tag.get('poster', '')

                if not src:
                    log_step(f"Skipping video with no src: {str(tag)}")
                    continue

                if not src.startswith('http'):
                    src = 'https://zdnet.co.kr' + src
                if poster and not poster.startswith('http'):
                    poster = 'https://zdnet.co.kr' + poster

                video_attrs = tag.attrs.copy()
                video_attrs['src'] = src
                if poster:
                    video_attrs['poster'] = poster
                video_attrs.setdefault('controls', '')
                video_attrs.setdefault('width', '720px')

                attr_strs = []
                for k, v in video_attrs.items():
                    if v == '' or v is True:
                        attr_strs.append(k)
                    else:
                        attr_strs.append(f'{k}="{v}"')

                video_tag = f"<video {' '.join(attr_strs)}></video>"
                elements.append(f'<p>{video_tag}</p>')
                video_urls.append(src)

            # Preserve paragraphs and captions
            elif tag.name in ['p', 'figcaption', 'h2', 'ul', 'ol', 'li', 'figure']:
                elements.append(str(tag))

        cleaned_html = ''.join(elements)

        # Try to get a featured image
        featured_image = None
        if image_urls:
            featured_image = image_urls[0]
            try:
                img_response = requests.head(featured_image, headers=headers, timeout=5)
                if img_response.status_code != 200:
                    featured_image = None
            except Exception as e:
                log_step(f"Error validating image {featured_image}: {e}")
                featured_image = None

        # Fallback: use video poster
        if not featured_image and content_root.find('video'):
            poster = content_root.find('video').get('poster', '')
            if poster and not poster.startswith('http'):
                poster = 'https://zdnet.co.kr' + poster
            try:
                poster_response = requests.head(poster, headers=headers, timeout=5)
                if poster_response.status_code == 200:
                    featured_image = poster
            except Exception as e:
                log_step(f"Error validating video poster {poster}: {e}")

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
