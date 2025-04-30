import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

TARGET_URL = 'https://www.todayhumor.co.kr'

def fetch_articles(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    items = []

    # Accurate selector for humor board
    links = soup.select('.main_table .subject a')
    for a in links:
        title = a.get_text(strip=True)
        href = a['href']
        full_link = 'https://www.todayhumor.co.kr' + href
        pub_date = datetime.now(timezone.utc).isoformat()

        items.append({
            'title': title,
            'link': full_link,
            'pubDate': pub_date,
        })

    return items

def generate_rss(items):
    fg = FeedGenerator()
    fg.title('TodayHumor - Humor Board')
    fg.link(href=TARGET_URL)
    fg.description('Latest posts from TodayHumor Humor Board')
    fg.language('ko')
    fg.lastBuildDate(datetime.now(timezone.utc))
    fg.generator('python-feedgen')

    for item in items:
        fe = fg.add_entry()
        fe.title(item['title'])
        fe.link(href=item['link'])
        fe.pubDate(item['pubDate'])
        fe.description(f'Read more: {item["link"]}')

    fg.rss_file('todayhumor.xml')
    print("✅ RSS feed created: custom_feed.xml")

if __name__ == '__main__':
    articles = fetch_articles(TARGET_URL)
    if articles:
        generate_rss(articles)
    else:
        print("❌ No articles found. Check selector or site availability.")
