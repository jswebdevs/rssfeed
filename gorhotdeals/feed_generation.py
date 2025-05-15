from lxml import etree
from datetime import datetime
from log import log_step
from bs4 import BeautifulSoup
import re
import mimetypes
import os
import requests

# Ensure feed.xml is written in the current folder (where this script is)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_FILE = os.path.join(BASE_DIR, "feed.xml")

def generate_rss_feed(items, output_file=FEED_FILE):
    rss = etree.Element("rss", version="2.0", nsmap={
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "wp": "http://wordpress.org/export/1.2/"
    })
    channel = etree.SubElement(rss, "channel")

    etree.SubElement(channel, "title").text = "Ggoorr RSS Feed"
    etree.SubElement(channel, "link").text = "https://ggoorr.net/"
    etree.SubElement(channel, "description").text = "RSS feed generated from ggoorr.net"
    etree.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    seen_guids = set()

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            log_step(f"Skipping invalid item at index {idx}: {item}")
            continue

        item_elem = etree.SubElement(channel, "item")

        title = (item.get('title') or '').strip() or f"Untitled Post {idx + 1}"
        link = (item.get('link') or '').strip() or f"https://ggoorr.net/placeholder/{idx + 1}"
        content = (item.get('content') or '').strip()
        featured_image = (item.get('featured_image') or '').strip()
        categories = item.get('categories', [])

        guid = link
        if guid in seen_guids:
            guid = f"{link}-{idx}"
            log_step(f"Duplicate GUID detected for link {link}, using {guid}")
        seen_guids.add(guid)

        log_step(f"Raw content for item {idx + 1}: {content[:500]}{'...' if len(content) > 500 else ''}")
        log_step(f"Featured image for item {idx + 1}: {featured_image}")
        log_step(f"Categories for item {idx + 1}: {categories}")

        modified_content = modify_content(content)

        soup = BeautifulSoup(modified_content, 'html.parser')
        plain_text = soup.get_text(strip=True)[:200]

        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src', '')
            if src:
                try:
                    response = requests.head(src, timeout=5)
                    log_step(f"Video URL {src} status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
                    if response.status_code != 200 or 'video/' not in response.headers.get('Content-Type', ''):
                        log_step(f"Warning: Video URL {src} may not be accessible or is not a video")
                except Exception as e:
                    log_step(f"Error validating video URL {src}: {str(e)}")

        log_step(f"Video tags for item {idx + 1}: {[str(v) for v in video_tags]}")

        log_step(
            f"==============\n"
            f"Item {idx + 1}:\n"
            f"title: {title}\n"
            f"link: {link}\n"
            f"guid: {guid}\n"
            f"content: {modified_content[:500]}{'...' if len(modified_content) > 500 else ''}\n"
            f"length: {len(modified_content)}\n"
            f"plain_text: {plain_text}\n"
            f"featured_image: {featured_image}\n"
            f"categories: {categories}\n"
            f"=============="
        )

        etree.SubElement(item_elem, "title").text = title
        etree.SubElement(item_elem, "link").text = link
        etree.SubElement(item_elem, "category").text = "모두"
        etree.SubElement(item_elem, "category").text = "기분"
        for category in categories:
            etree.SubElement(item_elem, "category").text = category
        etree.SubElement(item_elem, "{http://purl.org/dc/elements/1.1/}creator").text = "슈파슈파"
        etree.SubElement(item_elem, "guid", isPermaLink="true").text = guid

        description_elem = etree.SubElement(item_elem, "description")
        description_elem.text = plain_text or ""

        content_elem = etree.SubElement(item_elem, "{http://purl.org/rss/1.0/modules/content/}encoded")
        content_elem.text = etree.CDATA(modified_content) if modified_content else ""

        if featured_image and featured_image.startswith('http'):
            mime_type, _ = mimetypes.guess_type(featured_image)
            if not mime_type:
                mime_type = 'image/jpeg'
            etree.SubElement(item_elem, "enclosure", url=featured_image, type=mime_type, length="0")
            postmeta_elem = etree.SubElement(item_elem, "{http://wordpress.org/export/1.2/}postmeta")
            etree.SubElement(postmeta_elem, "meta_key").text = "_thumbnail_id"
            etree.SubElement(postmeta_elem, "meta_value").text = featured_image

    try:
        tree = etree.ElementTree(rss)
        tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
        log_step(f"RSS feed written to {output_file}, total items: {len(items)}")
    except Exception as e:
        log_step(f"Failed to write RSS feed: {str(e)}")


def modify_content(content):
    soup = BeautifulSoup(content, 'html.parser')
    modified_elements = []

    youtube_regex = r'(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    vimeo_regex = r'(?:vimeo\.com/(?:video/|embed/)?)(\d+)'

    for tag in soup.find_all(['p', 'img', 'video', 'iframe', 'a']):
        if tag.name == 'p':
            if tag.get_text(strip=True):
                modified_elements.append(str(tag))
        elif tag.name == 'img':
            img_url = tag.get('src', '')
            if img_url:
                img_attrs = tag.attrs.copy()
                img_tag = f"<img {' '.join(f'{k}=\"{v}\"' for k, v in img_attrs.items() if v is not None)}/>"
                modified_elements.append(f'</br>{img_tag}</br>')
            else:
                log_step(f"Skipping img tag with no src: {str(tag)}")
        elif tag.name == 'video':
            video_url = tag.get('src', '')
            if video_url:
                log_step(f"Input video tag attributes: {tag.attrs}")
                video_attrs = tag.attrs.copy()
                attr_strings = []
                for k, v in video_attrs.items():
                    if v is None:
                        continue
                    elif v == '' or v is True:
                        attr_strings.append(k)
                    else:
                        attr_strings.append(f'{k}="{v}"')
                video_tag = f"<video {' '.join(attr_strings)}></video>"
                modified_elements.append(f'</br>{video_tag}</br>')
                log_step(f"Output video tag: {video_tag}")
            else:
                log_step(f"Skipping video tag with no src: {str(tag)}")
        elif tag.name in ['iframe', 'a']:
            url = tag.get('src') if tag.name == 'iframe' else tag.get('href', '')
            if url:
                youtube_match = re.search(youtube_regex, url)
                vimeo_match = re.search(vimeo_regex, url)
                if youtube_match:
                    video_id = youtube_match.group(1)
                    iframe_tag = (
                        f'</br><iframe width="360px" height="auto" '
                        f'src="https://www.youtube.com/embed/{video_id}" '
                        f'frameborder="0" allowfullscreen></iframe></br>'
                    )
                    modified_elements.append(iframe_tag)
                elif vimeo_match:
                    video_id = vimeo_match.group(1)
                    iframe_tag = (
                        f'</br><iframe width="360px" height="auto" '
                        f'src="https://player.vimeo.com/video/{video_id}" '
                        f'frameborder="0" allowfullscreen></iframe></br>'
                    )
                    modified_elements.append(iframe_tag)
                else:
                    modified_elements.append(f'</br><a href="{url}">Watch Video</a></br>')

    return ''.join(modified_elements)