import asyncio
import datetime
import feedparser
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


requests.packages.urllib3.disable_warnings()
today = datetime.datetime.now().strftime("%Y-%m-%d")

def update_today(data: list=[]):
    """更新today"""
    root_path = Path(__file__).absolute().parent # 获取当前文件所在路径
    today_path = root_path.joinpath('today.md')
    archive_path = root_path.joinpath(f'archive/{today.split("-")[0]}/{today}.md')
    archive_path.parent.mkdir(parents=True, exist_ok=True) # 创建 archive/year目录
    
    # 保存两份：一份写入项目根目录，一份备份存档(archive)
    with open(today_path, 'w+') as f1, open(archive_path, 'w+') as f2:
        content = f'# 每日安全资讯（{today}）\n\n'
        for item in data:
            (feed, value), = item.items()
            content += f'- {feed}\n'
            for title, url in value.items():
                content += f'  - [{title}]({url})\n'
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
        r = requests.get(url, timeout=10, headers=headers)
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
    return title, result


async def job():
    # 读取rss订阅连接
    with open('feeds.txt', 'r', encoding='utf-8') as f:
        feeds = [line.strip() for line in f if line.strip()]  # 去除空行和空格

    # 去重:合并相同的订阅链接


    # 获取文章
    results = []
    numb = 0
    tasks = []
    with ThreadPoolExecutor(64) as executor:
        tasks.extend(executor.submit(parseThread, url) for url in feeds)
        for task in as_completed(tasks):
            title, result = task.result()            
            if result:
                numb += len(result.values())
                results.append({title: result})
    print(f'[+] {len(results)} feeds, {numb} articles')

    update_today(results)


async def main():
    await job()

if __name__ == '__main__':
    asyncio.run(main())