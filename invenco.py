import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

TARGET_URL = 'https://www.inven.co.kr'

def fetch_articles(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    items = []

    # Accurate selector for humor board
    links = soup.select('.title-txt')
    for a in links:
        title = a.get_text(strip=True)

        items.append({
            'title': title,
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


    fg.rss_file('inven.xml')
    print("✅ RSS feed created: custom_feed.xml")

if __name__ == '__main__':
    articles = fetch_articles(TARGET_URL)
    if articles:
        generate_rss(articles)
    else:
        print("❌ No articles found. Check selector or site availability.")
