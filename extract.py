from bs4 import BeautifulSoup


def extract_xml_urls_with_bs4(opml_file_path):
    """
    使用BeautifulSoup从OPML文件中提取xmlUrl
    
    Args:
        opml_file_path: OPML文件路径
        
    Returns:
        list: 包含所有xmlUrl的列表
    """
    try:
        with open(opml_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'xml')
        outlines = soup.find_all('outline')
        
        xml_urls = []
        for outline in outlines:
            xml_url = outline.get('xmlUrl')
            if xml_url:
                xml_urls.append(xml_url)
        
        return xml_urls
        
    except FileNotFoundError:
        print(f"文件未找到: {opml_file_path}")
        return []
    except Exception as e:
        print(f"发生错误: {e}")
        return []


# 使用示例
if __name__ == "__main__":
    opml_file = "rss/feeder-export-2026-08-22-61821.opml"
    urls = extract_xml_urls_with_bs4(opml_file)
    print(f"找到 {len(urls)} 个订阅链接:")
    try:
        with open("feeds.txt", 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        print(f"\n成功保存 {len(urls)} 个链接")
    except Exception as e:
        print(f"保存文件失败: {e}")