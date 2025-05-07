from lxml import etree
from datetime import datetime
from log import log_step
from bs4 import BeautifulSoup
import re

def generate_rss_feed(items, output_file="feed.xml"):
    # Create RSS root with dc and content namespaces
    rss = etree.Element("rss", version="2.0", nsmap={
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/"
    })
    channel = etree.SubElement(rss, "channel")

    # Channel metadata
    etree.SubElement(channel, "title").text = "Ggoorr RSS Feed"
    etree.SubElement(channel, "link").text = "https://ggoorr.net/"
    etree.SubElement(channel, "description").text = "RSS feed generated from ggoorr.net"
    etree.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Track GUIDs to ensure uniqueness
    seen_guids = set()

    for idx, item in enumerate(items):
        item_elem = etree.SubElement(channel, "item")

        title = item.get('title', '').strip() or f"Untitled Post {idx + 1}"
        link = item.get('link', '').strip() or f"https://ggoorr.net/placeholder/{idx + 1}"
        content = item.get('content', '').strip()

        # Ensure unique GUID
        guid = link
        if guid in seen_guids:
            guid = f"{link}-{idx}"
            log_step(f"Duplicate GUID detected for link {link}, using {guid}")
        seen_guids.add(guid)

        # Log raw content to verify input
        log_step(f"Raw content for item {idx + 1}: {content[:500]}{'...' if len(content) > 500 else ''}")

        # Modify content to match desired format
        modified_content = modify_content(content)

        # Create plain text description (truncate HTML-stripped content)
        soup = BeautifulSoup(modified_content, 'html.parser')
        plain_text = soup.get_text(strip=True)[:200]  # First 200 chars for description

        # Detailed log for debugging
        log_step(
            f"==============\n"
            f"Item {idx + 1}:\n"
            f"title: {title}\n"
            f"link: {link}\n"
            f"guid: {guid}\n"
            f"content: {modified_content}\n"
            f"length: {len(modified_content)}\n"
            f"plain_text: {plain_text}\n"
            f"=============="
        )

        # Item fields
        etree.SubElement(item_elem, "title").text = title
        etree.SubElement(item_elem, "link").text = link
        etree.SubElement(item_elem, "category").text = "유머/이슈"
        etree.SubElement(item_elem, "category").text = "최신"
        etree.SubElement(item_elem, "{http://purl.org/dc/elements/1.1/}creator").text = "슈파슈파"
        etree.SubElement(item_elem, "guid", isPermaLink="true").text = guid

        # Add description with plain text
        description_elem = etree.SubElement(item_elem, "description")
        description_elem.text = plain_text or ""

        # Add content:encoded with full HTML in CDATA
        content_elem = etree.SubElement(item_elem, "{http://purl.org/rss/1.0/modules/content/}encoded")
        if modified_content:
            content_elem.text = etree.CDATA(modified_content)
        else:
            content_elem.text = ""

    try:
        tree = etree.ElementTree(rss)
        tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
        log_step(f"RSS feed written to {output_file}, total items: {len(items)}")
    except Exception as e:
        log_step(f"Failed to write RSS feed: {str(e)}")

def modify_content(content):
    """Modify HTML content with original image URLs, video URLs, and YouTube/Vimeo embeds, no newlines."""
    soup = BeautifulSoup(content, 'html.parser')
    modified_elements = []

    # Regex for YouTube and Vimeo video IDs
    youtube_regex = r'(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    vimeo_regex = r'(?:vimeo\.com/(?:video/|embed/)?)(\d+)'

    for tag in soup.find_all(['p', 'img', 'video', 'iframe', 'a']):
        if tag.name == 'p':
            if tag.get_text(strip=True):  # Skip empty <p> tags
                modified_elements.append(str(tag))
        elif tag.name == 'img':
            # Use original image URL
            img_url = tag.get('src', '')
            if img_url:
                img_attrs = {
                    'width': tag.get('width', ''),
                    'height': tag.get('height', ''),
                    'src': img_url,
                    'alt': tag.get('alt', '')
                }
                img_tag = f"<img {' '.join(f'{k}=\"{v}\"' for k, v in img_attrs.items() if v)}/>"
                modified_elements.append(f'<p>{img_tag}</p>')
            else:
                log_step(f"Skipping img tag with no src: {str(tag)}")
        elif tag.name == 'video':
            # Use original video URL with minimal attributes
            video_url = tag.get('src', '')
            if video_url:
                video_attrs = {
                    'src': video_url,
                    'controls': 'controls',
                    'width': tag.get('width', '560'),
                    'height': tag.get('height', '315')
                }
                video_tag = f"<video {' '.join(f'{k}=\"{v}\"' for k, v in video_attrs.items() if v)}></video>"
                modified_elements.append(f'<p>{video_tag}</p>')
            else:
                log_step(f"Skipping video tag with no src: {str(tag)}")
        elif tag.name == 'iframe' or tag.name == 'a':
            # Check for YouTube or Vimeo URL
            url = tag.get('src') if tag.name == 'iframe' else tag.get('href', '')
            if url:
                youtube_match = re.search(youtube_regex, url)
                vimeo_match = re.search(vimeo_regex, url)
                if youtube_match:
                    video_id = youtube_match.group(1)
                    iframe_tag = (
                        f'<p><iframe width="560" height="315" '
                        f'src="https://www.youtube.com/embed/{video_id}" '
                        f'frameborder="0" allowfullscreen></iframe></p>'
                    )
                    modified_elements.append(iframe_tag)
                elif vimeo_match:
                    video_id = vimeo_match.group(1)
                    iframe_tag = (
                        f'<p><iframe width="560" height="315" '
                        f'src="https://player.vimeo.com/video/{video_id}" '
                        f'frameborder="0" allowfullscreen></iframe></p>'
                    )
                    modified_elements.append(iframe_tag)
                else:
                    # Fallback to link for unrecognized URLs
                    modified_elements.append(f'<p><a href="{url}">Watch Video</a></p>')

    # Join without newlines to prevent \n in WordPress
    return ''.join(modified_elements)