import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html
import xml.etree.ElementTree as ET

BASE_URL = "https://ggoorr.net"
TOTAL_PAGES = 5  # Test for one page
CATEGORY_NAME = "latest-posts"
AUTHOR = "addas"
XML_FILENAME = "ggoorr.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_post_links(page_num):
    url = f"{BASE_URL}/main/page/{page_num}"
    print(f"📄 Fetching page {page_num} from URL: {url}")
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to retrieve page {page_num}. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    for div in soup.find_all("div", class_="lddu-title-wrap"):
        a_tag = div.find("a", class_="lu-title lddu-title")
        if a_tag:
            href = a_tag.get("href", "").strip()
            full_url = urljoin(BASE_URL, href)
            title = a_tag.get_text(strip=True)
            links.append((title, full_url))
        else:
            print(f"⚠️ No title found in div: {div}")

    print(f"🔗 Found {len(links)} post links on page {page_num}")
    return links

def extract_post_data(title, url):
    print(f"🔗 Fetching post data for: {title} ({url})")
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to retrieve post {title}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find("div", class_="slatc-content")
    if not content_div:
        print(f"⚠️ No content found for post: {title}")
        return None

    content_html = str(content_div)
    first_img = content_div.find("img")
    if first_img:
        featured_image = first_img.get("src", "")
    else:
        featured_image = ""
        print(f"⚠️ No featured image found for post: {title}")

    content_html = clean_html(content_html)

    print(f"✅ Post data extracted for: {title}")
    return {
        "title": title,
        "content": content_html,
        "featured_image": featured_image
    }

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    for img_tag in soup.find_all('img'):
        img_tag.attrs = {'src': img_tag.get('src', '')}
    return str(soup)

def generate_xml(posts):
    print(f"📦 Generating XML file with {len(posts)} posts")
    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
        "xmlns:wfw": "http://wellformedweb.org/CommentAPI/",
        "xmlns:dc": "http://purl.org/dc/elements/1.1/",
        "xmlns:wp": "http://wordpress.org/export/1.2/"
    })
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "ggoorr import"
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "description").text = "Imported posts from ggoorr.net"

    author = ET.SubElement(channel, "wp:author")
    ET.SubElement(author, "wp:author_id").text = "1"
    ET.SubElement(author, "wp:author_login").text = AUTHOR

    for i, post in enumerate(posts):
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post["title"]
        ET.SubElement(item, "link").text = ""
        ET.SubElement(item, "pubDate").text = ""
        ET.SubElement(item, "dc:creator").text = AUTHOR
        ET.SubElement(item, "category", {"domain": "category", "nicename": CATEGORY_NAME}).text = CATEGORY_NAME
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = ""
        ET.SubElement(item, "description").text = ""
        ET.SubElement(item, "content:encoded").text = f"__CONTENT_{i}__"
        ET.SubElement(item, "excerpt:encoded").text = ""
        ET.SubElement(item, "wp:post_id").text = str(i + 1)
        ET.SubElement(item, "wp:post_date").text = ""
        ET.SubElement(item, "wp:post_date_gmt").text = ""
        ET.SubElement(item, "wp:comment_status").text = "closed"
        ET.SubElement(item, "wp:ping_status").text = "closed"
        ET.SubElement(item, "wp:post_name").text = ""
        ET.SubElement(item, "wp:status").text = "publish"
        ET.SubElement(item, "wp:post_parent").text = "0"
        ET.SubElement(item, "wp:menu_order").text = "0"
        ET.SubElement(item, "wp:post_type").text = "post"
        ET.SubElement(item, "wp:post_password").text = ""
        ET.SubElement(item, "wp:is_sticky").text = "0"

        if post["featured_image"]:
            postmeta = ET.SubElement(item, "wp:postmeta")
            ET.SubElement(postmeta, "wp:meta_key").text = "_thumbnail_url"
            ET.SubElement(postmeta, "wp:meta_value").text = post["featured_image"]

    xml_str = ET.tostring(rss, encoding="utf-8").decode("utf-8")
    for i, post in enumerate(posts):
        cdata = f"<![CDATA[{post['content']}]]>"
        xml_str = xml_str.replace(f"__CONTENT_{i}__", cdata)

    with open(XML_FILENAME, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_str)

    print(f"✅ XML file created: {XML_FILENAME}")

def main():
    all_posts = []
    for page in range(1, TOTAL_PAGES + 1):
        print(f"📄 Processing page {page}/{TOTAL_PAGES}")
        links = get_post_links(page)
        if not links:
            print(f"❌ No links found on page {page}")
            continue

        for title, link in links:
            print(f"🔗 Fetching post: {title}")
            post_data = extract_post_data(title, link)
            if post_data:
                all_posts.append(post_data)

    if all_posts:
        generate_xml(all_posts)
        print(f"✅ Total posts: {len(all_posts)}")
        print("XML file generated successfully.")
    else:
        print("❌ No posts to generate XML file.")

if __name__ == "__main__":
    main()
    print("🚀 Done!")
