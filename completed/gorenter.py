import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

BASE_URL = 'https://ggoorr.net'
TARGET_URL = 'https://ggoorr.net/enter'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
}

def fetch_article_content(full_url, mode='html'):
    try:
        response = requests.get(full_url, headers=HEADERS)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.select_one('.slatc-content')
        if not content_div:
            return "<p>No content found</p>", ['humor']

        # Fix image src paths
        for tag in content_div.find_all('img'):
            if tag.has_attr('src'):
                tag['src'] = urljoin(BASE_URL, tag['src'])

        # If only image list needed (as readable HTML)
        if mode == 'list':
            img_urls = [tag['src'] for tag in content_div.find_all('img') if tag.has_attr('src')]
            img_tags = "".join([f'<img src="{src}" style="max-width:100%;"><br>' for src in img_urls])
            return f"<div>{img_tags}</div>", ['humor']

        # Clean content, keeping only p, div, img
        for tag in content_div.find_all():
            if tag.name not in ['p', 'div', 'img']:
                tag.decompose()

        content_html = str(content_div)
        return content_html, ['humor']

    except Exception as e:
        return f"<p>Error fetching content: {e}</p>", ['humor']

def fetch_articles(main_url):
    response = requests.get(main_url, headers=HEADERS)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []

    links = soup.select('ul.lwu-wrap a.lwnu-title')

    for a in links:
        href = a['href']
        full_link = urljoin(BASE_URL, href)
        title = a.get_text(strip=True)
        pub_date = datetime.now(timezone.utc)

        content, categories = fetch_article_content(full_link, mode='list')

        items.append({
            'title': title,
            'link': full_link,
            'pubDate': pub_date.strftime('%a, %d %b %Y %H:%M:%S +0000'),
            'categories': ['humor'],  # forcefully fix category to only "humor"
            'content': content
        })

    return items

def generate_rss(items):
    fg = FeedGenerator()
    fg.title('Ggoorr Humor Feed')
    fg.link(href=BASE_URL)
    fg.description('Latest humor posts from Ggoorr')
    fg.language('ko')
    fg.lastBuildDate(datetime.now(timezone.utc))
    fg.generator('python-feedgen')

    for item in items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['pubDate'])
        fe.description(item['content'])  # For WordPress, use description()

        for cat in item['categories']:
            fe.category(term='humor')  # Ensure exactly "humor"

    fg.rss_file('gorenter.xml', pretty=True)
    print("✅ RSS feed created: gorenter.xml")

if __name__ == '__main__':
    articles = fetch_articles(TARGET_URL)
    if articles:
        generate_rss(articles)
