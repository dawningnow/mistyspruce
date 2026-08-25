import asyncio
import datetime
import feedparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo


requests.packages.urllib3.disable_warnings()
today = datetime.datetime.now().strftime("%Y-%m-%d")


def update_today(data: list=[]):
    """更新today"""
    hour = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).hour
    root_path = Path(__file__).absolute().parent # 获取当前文件所在路径
    today_path = root_path.joinpath('today.md')
    if hour < 18:
        archive_path = root_path.joinpath(f'archive/{today.split("-")[0]}/{today.split("-")[1]}/{today}-daytime.md')
    else:
        archive_path = root_path.joinpath(f'archive/{today.split("-")[0]}/{today.split("-")[1]}/{today}-evening.md')
    archive_path.parent.mkdir(parents=True, exist_ok=True) # 创建 archive/year/mons目录
    
    # 保存两份：一份写入项目根目录，一份备份存档(archive)
    with open(today_path, 'w+') as f1, open(archive_path, 'w+') as f2:
        content = f'# Daily News({today})\n\n'
        for item in data:
            (feed, value), = item.items()
            content += f'**{feed}**\n'
            for index, (title, url) in enumerate(value.items()):
                content += f' {index + 1}. [{title}]({url})\n'
            content += "\n"
        f1.write(content)
        f2.write(content)


def parseThread(url: str):
    """获取文章线程"""

    headers = headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    title = ''
    result = {}
    try:
        r = requests.get(url, timeout=36, headers=headers)
        r = feedparser.parse(r.content)
        title = r.feed.title # 保存订阅源的名称
        for entry in r.entries:
            d = entry.get('published_parsed') or entry.get('updated_parsed')
            yesterday = datetime.date.today() + datetime.timedelta(-1)  # -1:日期往前推一天，也就是昨天
            pubday = datetime.date(d[0], d[1], d[2]) # 获取发布日期
            if pubday == yesterday:
                item = {entry.title: entry.link} # 保存标题和链接
                result |= item
    except Exception as e:
        print(f'[-] failed: {url}')
        print(e)
    return url, title, result


def get_feeds():
    feeds = []
    feed_domains = set()  # 存储简化域名用于快速查找
    for file_path in Path("./rss").glob('*.opml'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'xml')
                for outline in soup.find_all('outline'):
                    xml_url = outline.get('xmlUrl')
                    if xml_url:
                        url = xml_url.strip().rstrip('/')  
                        short_url = url.split('://')[-1].split('www.')[-1]
                        if short_url not in feed_domains:  # O(1) 查找
                            feeds.append(url)
                            feed_domains.add(short_url)  # 记录已存在的域名
        except Exception as e:
            print(f"处理文件 {file_path.name} 时出错: {e}")
    
    return feeds


async def job():
    # 获取订阅源url
    feeds = get_feeds()

    # 获取文章
    results = []
    numb = 0
    futures = []
    false_feeds = []
    with ThreadPoolExecutor(64) as executor:
        futures.extend(executor.submit(parseThread, url) for url in feeds)
        for future in as_completed(futures):
            url, title, result = future.result() 
            if result:
                numb += len(result.values())
                results.append({title: result})
            else:
                false_feeds.append({'title':title, 'url':url})
    print(f'[+] {len(results)} feeds, {numb} articles')

    update_today(results)

    # 保存读取失败的feed
    with open("today_false.md", 'w+') as f1:
        content = f'# Failed to obtain({today})\n'
        for index, feed in enumerate(false_feeds):
            title, url = feed.get('title'), feed.get('url')
            if not title:
                title = "Unknown"
            content += f'{index + 1}. [{title}]({url})\n'
        f1.write(content)

async def main():
    await job()


if __name__ == '__main__':
    asyncio.run(main())