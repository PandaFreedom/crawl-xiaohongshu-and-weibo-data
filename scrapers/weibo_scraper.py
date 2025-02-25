import requests
import json
import time
import random
from fake_useragent import UserAgent
import pandas as pd
from datetime import datetime
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WeiboScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            'User-Agent': self.ua.random,
            'Cookie': '0a00d77517403723530526190e78f19ba48b60c3c7c84b1fcd6d106d84aa48',  # 这里需要填入微博的 Cookie
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.search_url = "https://m.weibo.cn/api/container/getIndex"
        self.data_path = "data/weibo"
        os.makedirs(self.data_path, exist_ok=True)

    def search_weibo(self, keyword, page):
        """
        搜索微博
        """
        params = {
            'containerid': '100103type=1&q=' + keyword,
            'page_type': 'searchall',
            'page': page
        }
        
        try:
            response = requests.get(
                self.search_url,
                headers=self.headers,
                params=params
            )
            return response.json()
        except Exception as e:
            print(f"搜索出错: {e}")
            return None

    def parse_weibo(self, card):
        """
        解析微博数据
        """
        mblog = card.get('mblog', {})
        return {
            '内容': mblog.get('text', ''),
            '转发数': mblog.get('reposts_count', 0),
            '评论数': mblog.get('comments_count', 0), 
            '点赞数': mblog.get('attitudes_count', 0),
            '用户名': mblog.get('user', {}).get('screen_name', ''),
            '发布时间': mblog.get('created_at', ''),
            '微博ID': mblog.get('id', '')
        }

    def scrape_and_save(self, keyword, max_pages=10):
        """
        爬取并保存数据
        """
        all_weibos = []
        
        for page in range(1, max_pages + 1):
            print(f"正在爬取第 {page} 页...")
            data = self.search_weibo(keyword, page)
            
            if not data or 'data' not in data or 'cards' not in data['data']:
                break
                
            cards = data['data']['cards']
            for card in cards:
                if card.get('card_type') == 9:  # 微博卡片类型
                    parsed_weibo = self.parse_weibo(card)
                    all_weibos.append(parsed_weibo)
            
            # 随机延迟，避免被封
            time.sleep(random.uniform(2, 5))
        
        # 保存为Excel格式
        if all_weibos:
            df = pd.DataFrame(all_weibos)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.data_path}/weibo_{keyword}_{timestamp}.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"数据已保存到: {filename}")
            return df
        return None

    def analyze_data(self, df):
        """
        简单的数据分析
        """
        if df is None or df.empty:
            return
            
        print("\n=== 数据分析结果 ===")
        print(f"总微博数: {len(df)}")
        print(f"平均转发数: {df['reposts_count'].mean():.2f}")
        print(f"平均评论数: {df['comments_count'].mean():.2f}")
        print(f"平均点赞数: {df['attitudes_count'].mean():.2f}")
        
        # 互动率最高的前5条微博
        df['interaction_rate'] = df['reposts_count'] + df['comments_count'] + df['attitudes_count']
        top_weibos = df.nlargest(5, 'interaction_rate')
        print("\n互动率最高的5条微博：")
        for _, weibo in top_weibos.iterrows():
            print(f"作者: {weibo['user_name']}")
            print(f"内容: {weibo['content'][:100]}...")
            print(f"互动数: 转发{weibo['reposts_count']}, 评论{weibo['comments_count']}, 点赞{weibo['attitudes_count']}")
            print("---")

if __name__ == "__main__":
    scraper = WeiboScraper()
    keyword = "哈尔滨冰雪大世界"
    df = scraper.scrape_and_save(keyword)
    scraper.analyze_data(df) 