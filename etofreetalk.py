
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

BASE_URL = 'https://www.etoland.co.kr/'
TARGET_URL = 'https://www.etoland.co.kr/bbs/board.php?bo_table=freebbs'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
}

def fetch_article_content(full_url):
    try:
        response = requests.get(full_url, headers=HEADERS)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        # Correct ID selector based on your example
        content_div = soup.select_one('#view_content')
        if not content_div:
            return "<p>No content found</p>", ['freetalk']

        # Fix image sources to be absolute URLs
        for tag in content_div.find_all('img'):
            if tag.has_attr('src'):
                tag['src'] = urljoin(BASE_URL, tag['src'])

        # Optionally remove scripts, styles, etc.
        for tag in content_div(['script', 'style']):
            tag.decompose()

        content_html = str(content_div)
        return content_html, ['freetalk']
    except Exception as e:
        return f"<p>Error fetching content: {e}</p>", ['freetalk']


def fetch_articles(main_url):
    response = requests.get(main_url, headers=HEADERS)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []

    # Select all <a> tags that are inside <li> and have .singleLineText
    links = soup.select('li a:has(.singleLineText)')

    for a in links:
        href = a.get('href')
        if not href:
            continue  # Skip if href is missing

        full_link = urljoin(BASE_URL, href)
        title_span = a.select_one('.singleLineText')
        title = title_span.get_text(strip=True) if title_span else 'Untitled'
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
    fg.title('Eto freetalk Feed')
    fg.link(href=BASE_URL)
    fg.description('Latest freetalk posts from etoland')
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

    fg.rss_file('etofreetalk.xml')
    print("✅ RSS feed created: etofreetalk.xml")

if __name__ == '__main__':
    articles = fetch_articles(TARGET_URL)
    if articles:
        generate_rss(articles)
