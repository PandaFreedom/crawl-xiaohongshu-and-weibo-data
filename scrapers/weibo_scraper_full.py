import requests
import json
import time
import random
from fake_useragent import UserAgent
import pandas as pd
from datetime import datetime
import os
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WeiboScraper")

class WeiboScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            'User-Agent': self.ua.random,
            'Cookie': '0a00d77517403723530526190e78f19ba48b60c3c7c84b1fcd6d106d84aa48',  # 这里需要填入微博的 Cookie
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D'
        }
        self.search_url = "https://m.weibo.cn/api/container/getIndex"
        self.data_path = "data/weibo"
        os.makedirs(self.data_path, exist_ok=True)
        self.max_retries = 5  # 最大重试次数

    def _update_user_agent(self):
        """随机更新User-Agent"""
        self.headers['User-Agent'] = self.ua.random
        return self.headers

    def search_weibo(self, keyword, page, retry_count=0):
        """
        搜索微博，增加重试机制
        """
        params = {
            'containerid': '100103type=1&q=' + keyword,
            'page_type': 'searchall',
            'page': page
        }
        
        try:
            # 每次请求都更新User-Agent
            headers = self._update_user_agent()
            logger.info(f"开始请求页面 {page}")
            
            response = requests.get(
                self.search_url,
                headers=headers,
                params=params,
                timeout=15  # 设置超时时间
            )
            
            if response.status_code != 200:
                logger.warning(f"页面 {page} 请求失败，状态码: {response.status_code}")
                if retry_count < self.max_retries:
                    retry_delay = 5 + random.uniform(1, 5) * retry_count
                    logger.info(f"将在 {retry_delay:.2f} 秒后重试...")
                    time.sleep(retry_delay)
                    return self.search_weibo(keyword, page, retry_count + 1)
                else:
                    logger.error(f"页面 {page} 达到最大重试次数，放弃请求")
                    return None
            
            json_data = response.json()
            return json_data
        except Exception as e:
            logger.error(f"请求出错: {e}")
            if retry_count < self.max_retries:
                retry_delay = 5 + random.uniform(1, 5) * retry_count
                logger.info(f"将在 {retry_delay:.2f} 秒后重试...")
                time.sleep(retry_delay)
                return self.search_weibo(keyword, page, retry_count + 1)
            else:
                logger.error(f"页面 {page} 达到最大重试次数，放弃请求")
                return None

    def parse_weibo(self, card):
        """
        解析微博数据
        """
        mblog = card.get('mblog', {})
        
        # 处理转发的微博
        retweeted_status = mblog.get('retweeted_status', {})
        original_text = ""
        if retweeted_status:
            original_text = retweeted_status.get('text', '')
        
        created_at = mblog.get('created_at', '')
        
        return {
            '内容': mblog.get('text', ''),
            '原微博内容': original_text,
            '转发数': mblog.get('reposts_count', 0),
            '评论数': mblog.get('comments_count', 0), 
            '点赞数': mblog.get('attitudes_count', 0),
            '用户名': mblog.get('user', {}).get('screen_name', ''),
            '用户ID': mblog.get('user', {}).get('id', ''),
            '发布时间': created_at,
            '微博ID': mblog.get('id', ''),
            '微博来源': mblog.get('source', '')
        }

    def scrape_and_save(self, keyword, max_pages=None, save_interval=20):
        """
        爬取并保存数据
        参数:
            keyword: 搜索关键词
            max_pages: 最大页数，None表示爬取所有可用页面
            save_interval: 每爬取多少页保存一次数据
        """
        all_weibos = []
        page = 1
        empty_page_count = 0  # 连续空页计数
        
        logger.info(f"开始爬取关键词: {keyword}")
        
        while True:
            logger.info(f"正在爬取第 {page} 页...")
            data = self.search_weibo(keyword, page)
            
            # 检查是否成功获取数据
            if not data or 'data' not in data:
                logger.warning(f"第 {page} 页无法获取数据")
                empty_page_count += 1
                if empty_page_count >= 3:  # 连续3页没有数据，认为已到达末尾
                    logger.info("连续多页无数据，认为已爬取完毕")
                    break
                page += 1
                time.sleep(random.uniform(3, 6))
                continue
            
            # 检查是否有卡片数据
            cards = data.get('data', {}).get('cards', [])
            
            if not cards:
                logger.warning(f"第 {page} 页没有微博卡片")
                empty_page_count += 1
                if empty_page_count >= 3:
                    logger.info("连续多页无卡片，认为已爬取完毕")
                    break
                page += 1
                time.sleep(random.uniform(3, 6))
                continue
            
            # 重置空页计数
            empty_page_count = 0
            
            # 解析微博内容
            weibos_count = 0
            for card in cards:
                if card.get('card_type') == 9:  # 微博卡片类型
                    parsed_weibo = self.parse_weibo(card)
                    all_weibos.append(parsed_weibo)
                    weibos_count += 1
            
            logger.info(f"第 {page} 页成功解析 {weibos_count} 条微博")
            
            # 检查是否达到最大页数
            if max_pages and page >= max_pages:
                logger.info(f"已达到设定的最大页数 {max_pages}，停止爬取")
                break
                
            # 每爬取一定页数，保存一次数据，避免爬取中断导致数据丢失
            if page % save_interval == 0 and all_weibos:
                self._save_interim_data(keyword, all_weibos, page)
            
            # 随机延迟，避免被封
            delay = random.uniform(3, 7)
            if page % 10 == 0:  # 每10页增加额外延迟
                delay = random.uniform(10, 15)
                logger.info(f"已爬取 {page} 页，增加额外延迟 {delay:.2f} 秒...")
            else:
                logger.info(f"页面切换延迟 {delay:.2f} 秒...")
            time.sleep(delay)
            
            page += 1
            
            # 检查是否已经没有更多数据（通过API返回的总数信息）
            if 'cardlistInfo' in data.get('data', {}) and 'page' in data['data']['cardlistInfo']:
                current_page = data['data']['cardlistInfo'].get('page', 1)
                # 如果API返回的当前页码小于我们正在请求的页码，说明已经到达末尾
                if current_page < page:
                    logger.info(f"API返回页码 {current_page} 小于请求页码 {page}，判断爬取完毕")
                    break
        
        # 保存最终数据
        if all_weibos:
            df = self._save_final_data(keyword, all_weibos)
            logger.info(f"爬取完成，共获取 {len(all_weibos)} 条微博数据")
            return df
        else:
            logger.warning("未获取到任何微博数据")
            return None
    
    def _save_interim_data(self, keyword, weibos, current_page):
        """保存中间数据"""
        df = pd.DataFrame(weibos)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.data_path}/interim_weibo_{keyword}_page{current_page}_{timestamp}.xlsx"
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"已保存中间数据到: {filename}")
    
    def _save_final_data(self, keyword, weibos):
        """保存最终数据"""
        df = pd.DataFrame(weibos)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.data_path}/weibo_{keyword}_complete_{timestamp}.xlsx"
        
        # 保存Excel格式
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"全部数据已保存到: {filename}")
        
        # 同时保存CSV格式，便于后续处理
        csv_filename = f"{self.data_path}/weibo_{keyword}_complete_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        logger.info(f"CSV格式数据已保存到: {csv_filename}")
        
        return df

    def analyze_data(self, df):
        """
        简单的数据分析
        """
        if df is None or df.empty:
            logger.warning("没有数据可供分析")
            return
            
        logger.info("\n=== 数据分析结果 ===")
        logger.info(f"总微博数: {len(df)}")
        
        try:
            logger.info(f"平均转发数: {df['转发数'].mean():.2f}")
            logger.info(f"平均评论数: {df['评论数'].mean():.2f}")
            logger.info(f"平均点赞数: {df['点赞数'].mean():.2f}")
            
            # 互动率最高的前10条微博
            df['互动率'] = df['转发数'] + df['评论数'] + df['点赞数']
            top_weibos = df.nlargest(10, '互动率')
            logger.info("\n互动率最高的10条微博：")
            for _, weibo in top_weibos.iterrows():
                logger.info(f"作者: {weibo['用户名']}")
                logger.info(f"内容: {weibo['内容'][:100]}...")
                logger.info(f"互动数: 转发{weibo['转发数']}, 评论{weibo['评论数']}, 点赞{weibo['点赞数']}")
                logger.info("---")
        except Exception as e:
            logger.error(f"分析数据时出错: {e}")

if __name__ == "__main__":
    scraper = WeiboScraper()
    keyword = "哈尔滨冰雪大世界"
    # 不设置max_pages参数，表示爬取所有可用页面
    df = scraper.scrape_and_save(keyword)
    scraper.analyze_data(df)