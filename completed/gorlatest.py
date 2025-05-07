import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

BASE_URL = 'https://ggoorr.net'
TARGET_URL = 'https://ggoorr.net/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
}

def fetch_article_content(full_url):
    try:
        response = requests.get(full_url, headers=HEADERS)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')

        content_div = soup.select_one('.slatc-content')
        if not content_div:
            return "<p>No content found.</p>", ['유머/이슈']

        # Get the full raw HTML as string
        raw_html = str(content_div)

        # Parse again to modify it cleanly
        content_soup = BeautifulSoup(raw_html, 'html.parser')

        # Fix image src and clean attributes
        for img in content_soup.find_all('img'):
            src = img.get('src', '')
            if src.startswith('/files'):
                # Convert to full CDN path
                full_src = urljoin('https://cdn.ggoorr.net', src)
                img['src'] = full_src

            # Remove unwanted attributes (keep only 'src', 'alt', 'width', 'height')
            for attr in list(img.attrs):
                if attr not in ['src', 'alt', 'width', 'height']:
                    del img[attr]

        # Remove lazy loading-related tags/attributes from all elements
        for tag in content_soup.find_all():
            for attr in ['loading', 'fetchpriority', 'data-cke-saved-src']:
                tag.attrs.pop(attr, None)

        # Done! Return cleaned HTML
        return str(content_soup), ['유머/이슈']

    except Exception as e:
        return f"<p>Error fetching content: {e}</p>", ['유머/이슈']

def fetch_articles(main_url):
    response = requests.get(main_url, headers=HEADERS)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    items = []

    # Get article links from the page
    links = soup.select('ul.lwu-wrap a.lwnu-title')

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
    fg.title('Ggoorr Latest Feed')
    fg.link(href=BASE_URL)
    fg.description('Latest posts from Ggoorr')
    fg.language('ko')
    fg.lastBuildDate(datetime.now(timezone.utc))
    fg.generator('python-feedgen')

    for item in items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['pubDate'])
        fe.content(item['content'])  # Use content() to add the full HTML content (including images)

        for cat in item['categories']:
            fe.category(term=cat)

    fg.rss_file('gorlatest.xml')
    print("✅ RSS feed created: gorlatest.xml")

if __name__ == '__main__':
    articles = fetch_articles(TARGET_URL)
    if articles:
        generate_rss(articles)
