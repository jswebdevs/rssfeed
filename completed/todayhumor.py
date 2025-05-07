import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from urllib.parse import urljoin

BASE_URL = 'https://www.todayhumor.co.kr'

def fetch_article_content(full_url):
    try:
        response = requests.get(full_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Full post content
        content_div = soup.select_one('.contentContainer')
        if not content_div:
            return "No content found", []

        # Fix relative image and media paths
        for tag in content_div.find_all(['img', 'video', 'source']):
            if tag.has_attr('src'):
                tag['src'] = urljoin(BASE_URL, tag['src'])

        content_html = str(content_div)

        # Extract categories (usually from meta or navigation)
        categories = []
        category_tag = soup.select_one('meta[property="og:title"]')
        if category_tag and category_tag.has_attr('content'):
            title = category_tag['content']
            if '[' in title and ']' in title:
                inside_brackets = title.split('[')[-1].split(']')[0]
                categories.append(inside_brackets.strip())

        categories.append('humor')  # Always include humor

        return content_html, categories
    except Exception as e:
        return f"<p>Error fetching content: {e}</p>", ['humor']

def fetch_articles(main_url):
    response = requests.get(main_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    items = []

    # Get post links and titles
    links = soup.select('.main_table .subject a')
    for a in links:
        title = a.get_text(strip=True)
        href = a['href']
        full_link = urljoin(BASE_URL, href)
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
    fg.title('TodayHumor - Humor Board')
    fg.link(href=BASE_URL)
    fg.description('Latest posts from TodayHumor Humor Board')
    fg.language('ko')
    fg.lastBuildDate(datetime.now(timezone.utc))
    fg.generator('python-feedgen')

    for item in items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['pubDate'])
        fe.description(item['content'])

        for cat in item['categories']:
            fe.category(term=cat)

    fg.rss_file('todayhumor.xml')
    print("✅ RSS feed created: todayhumor.xml")

if __name__ == '__main__':
    articles = fetch_articles(BASE_URL)
    if articles:
        generate_rss(articles)
    else:
        print("❌ No articles found. Check selector or site availability.")
