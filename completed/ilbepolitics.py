import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin
import urllib3

# Disable SSL certificate warnings (unsafe)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://www.ilbe.com/'
TARGET_URL = 'https://www.ilbe.com/list/polilbe'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
}

def fetch_article_content(full_url):
    try:
        response = requests.get(full_url, headers=HEADERS, verify=False)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.select_one('.post-content')
        if not content_div:
            return "No content found", []

        # Fix relative image and media paths
        for tag in content_div.find_all(['img']):
            if tag.has_attr('src'):
                tag['src'] = urljoin(BASE_URL, tag['src'])

        # Remove unwanted tags, keep only images, paragraphs, and divs
        for tag in content_div.find_all():
            if tag.name not in ['img', 'p', 'div']:
                tag.decompose()

        content_html = str(content_div)
        return content_html, ['politics']
    except Exception as e:
        return f"<p>Error fetching content: {e}</p>", ['politics']

def fetch_articles(main_url):
    response = requests.get(main_url, headers=HEADERS, verify=False)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []

    links = soup.select('a.subject')

    for a in links:
        href = a['href']
        full_link = urljoin(BASE_URL, href)
        title = a.get_text(strip=True)
        pub_date = datetime.now(timezone.utc).isoformat()

        content, categories = fetch_article_content(full_link)

        items.append({
            'title': title,
            'link': full_link,
            'pubDate': pub_date,
            'categories': categories,
            'content': content
        })

    return items

def generate_rss(items):
    fg = FeedGenerator()
    fg.title('ilbe politics Feed')
    fg.link(href=BASE_URL)
    fg.description('Latest politics posts from ilbe')
    fg.language('ko')
    fg.lastBuildDate(datetime.now(timezone.utc))
    fg.generator('python-feedgen')

    for item in items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['pubDate'])
        fe.content(item['content'])

        for cat in item['categories']:
            fe.category(term=cat)

    fg.rss_file('ilbepolitics.xml')
    print("✅ RSS feed created: ilbepolitics.xml")

if __name__ == '__main__':
    articles = fetch_articles(TARGET_URL)
    if articles:
        generate_rss(articles)
