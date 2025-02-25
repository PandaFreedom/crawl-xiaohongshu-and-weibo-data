from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
import pandas as pd
from datetime import datetime, timedelta
import os
import threading
import sys
import re

class XiaohongshuScraper:
    def __init__(self):
        self.chrome_options = Options()
        # self.chrome_options.add_argument('--headless')  # 先不使用无头模式，方便调试
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 修改保存路径，使用绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(os.path.dirname(current_dir), "data", "xiaohongshu")
        os.makedirs(self.data_path, exist_ok=True)
        print(f"数据将保存到: {self.data_path}")
        self.is_running = True  # 添加运行状态标志
        self.paused = False    # 添加暂停状态标志

    def init_driver(self):
        """
        初始化浏览器驱动
        """
        driver = webdriver.Chrome(options=self.chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        driver.implicitly_wait(10)
        return driver

    def scroll_page(self, driver):
        """
        滚动页面加载更多内容
        """
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def parse_note(self, element):
        try:
            print("\n尝试解析笔记...")
            
            # 获取标题
            try:
                title = element.find_element(By.CSS_SELECTOR, 'h3').text
            except:
                try:
                    title = element.find_element(By.CSS_SELECTOR, '.title').text
                except:
                    try:
                        title = element.find_element(By.CSS_SELECTOR, '.content').text
                    except:
                        try:
                            # 尝试获取链接的文本
                            title = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('title')
                        except:
                            title = "未知标题"
            print(f"找到标题: {title}")

            # 获取用户名
            try:
                user = element.find_element(By.CSS_SELECTOR, '.name').text
            except:
                try:
                    user = element.find_element(By.CSS_SELECTOR, '.author').text
                except:
                    user = "未知用户"
            print(f"找到用户: {user}")

            # 获取笔记链接
            try:
                link = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except:
                link = ""

            # 1. 获取互动数据
            try:
                # 获取所有数字元素
                count_elements = element.find_elements(By.CSS_SELECTOR, '.count, .like, .comment, .collect')
                
                likes, comments, collects = 0, 0, 0
                for elem in count_elements:
                    try:
                        # 获取父元素的完整HTML
                        parent = elem.find_element(By.XPATH, '..')
                        parent_html = parent.get_attribute('outerHTML').lower()
                        text = elem.text.strip()
                        
                        # 打印调试信息
                        print(f"互动元素: {text}, 父元素: {parent_html}")
                        
                        # 根据父元素HTML判断类型
                        if any(word in parent_html for word in ['like', '点赞']):
                            likes = self._convert_count(text)
                        elif any(word in parent_html for word in ['comment', '评论']):
                            comments = self._convert_count(text)
                        elif any(word in parent_html for word in ['collect', '收藏']):
                            collects = self._convert_count(text)
                    except Exception as e:
                        print(f"处理单个互动元素时出错: {e}")
                        continue
                
                print(f"解析到的互动数据: 点赞{likes}, 评论{comments}, 收藏{collects}")
                
            except Exception as e:
                print(f"获取互动数据时出错: {e}")
                likes, comments, collects = 0, 0, 0

            # 2. 获取发布时间
            try:
                # 尝试多个可能的时间选择器
                time_selectors = [
                    '.time',
                    '.date',
                    '.publish-time',
                    'time',
                    '.desc time',
                    '.desc',  # 可能在描述文本中包含时间
                    '.content'  # 可能在内容中包含时间
                ]
                
                time_text = None
                for selector in time_selectors:
                    try:
                        elements = element.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            text = elem.text
                            print(f"可能的时间文本: {text}")
                            # 检查文本是否包含时间相关信息
                            if any(word in text for word in ['年', '月', '日', '天前', '小时前']):
                                time_text = text
                                break
                        if time_text:
                            break
                    except:
                        continue
                
                if not time_text:
                    print("未找到时间信息，使用当前时间")
                    publish_date = datetime.now().strftime('%Y-%m-%d')
                else:
                    # 解析时间文本
                    date = None
                    if '年' in time_text and '月' in time_text:
                        # 提取年月日
                        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})?日?', time_text)
                        if match:
                            year = int(match.group(1))
                            month = int(match.group(2))
                            day = int(match.group(3)) if match.group(3) else 1
                            date = datetime(year, month, day)
                    elif '天前' in time_text:
                        days = int(re.search(r'(\d+)天前', time_text).group(1))
                        date = datetime.now() - timedelta(days=days)
                    elif '小时前' in time_text or '分钟前' in time_text:
                        date = datetime.now()
                    
                    if date:
                        # 检查日期范围
                        start_date = datetime(2022, 7, 1)
                        end_date = datetime(2023, 12, 31)
                        if start_date <= date <= end_date:
                            publish_date = date.strftime('%Y-%m-%d')
                        else:
                            print(f"日期 {date.strftime('%Y-%m-%d')} 不在目标范围内")
                            return None
                    else:
                        publish_date = datetime.now().strftime('%Y-%m-%d')
                    
                print(f"最终发布时间: {publish_date}")
                
            except Exception as e:
                print(f"处理时间信息时出错: {e}")
                publish_date = datetime.now().strftime('%Y-%m-%d')

            return {
                '标题': title,
                '用户名': user,
                '点赞数': likes,
                '评论数': comments,
                '收藏数': collects,
                '链接': link,
                '发布时间': publish_date
            }
        except Exception as e:
            print(f"解析笔记数据出错: {e}")
            return None

    def _convert_count(self, count_str):
        """
        转换计数字符串为数字
        例：'1.2w' -> 12000
        """
        try:
            if 'w' in count_str:
                return int(float(count_str.replace('w', '')) * 10000)
            elif 'k' in count_str:
                return int(float(count_str.replace('k', '')) * 1000)
            return int(count_str)
        except:
            return 0

    def keyboard_listener(self):
        """
        监听键盘输入
        """
        while self.is_running:
            try:
                if sys.stdin.readline().strip().lower() == 'p':
                    self.paused = not self.paused
                    if self.paused:
                        print("\n>>> 爬虫已暂停，按 'p' 继续爬取...")
                    else:
                        print("\n>>> 爬虫继续运行...")
            except Exception:
                pass

    def scrape_and_save(self, keyword, max_notes=100):
        driver = self.init_driver()
        all_notes = []
        save_counter = 0
        
        try:
            print("\n开始访问小红书...")
            print("提示：随时可以按 'p' 键暂停/继续爬取")
            print("仅收集2022年7月至2023年12月的数据")
            search_url = f"https://www.xiaohongshu.com/search?keyword={keyword}"
            driver.get(search_url)
            
            print("\n请在打开的浏览器窗口中手动登录小红书...")
            print("登录完成后，请按回车键继续...")
            input()
            
            print("\n继续执行爬取...")
            print(f"开始搜索关键词：{keyword}")
            
            # 确保保存目录存在
            os.makedirs(self.data_path, exist_ok=True)
            
            while len(all_notes) < max_notes and self.is_running:
                if self.paused:
                    time.sleep(1)
                    continue
                
                note_elements = driver.find_elements(By.CSS_SELECTOR, '.note-item')
                print(f"\n当前页面找到 {len(note_elements)} 个笔记")
                
                for element in note_elements:
                    if len(all_notes) >= max_notes:
                        break
                        
                    note_data = self.parse_note(element)
                    if note_data:  # 只有当解析成功时才添加数据
                        print("\n成功解析的数据:")
                        for key, value in note_data.items():
                            print(f"{key}: {value}")
                        
                        all_notes.append(note_data)
                        save_counter += 1
                        print(f"成功解析第 {len(all_notes)} 个笔记")
                        
                        # 每爬取3条数据就保存一次
                        if save_counter >= 3:
                            try:
                                self._save_to_excel(all_notes, keyword)
                                print(f"已保存 {len(all_notes)} 条数据")
                                save_counter = 0
                            except Exception as e:
                                print(f"保存数据时出错: {e}")
                
                # 滚动页面加载更多内容
                self.scroll_page(driver)
                time.sleep(random.uniform(2, 3))
        
        except Exception as e:
            print(f"爬取过程出错: {e}")
        
        finally:
            self.is_running = False
            driver.quit()
            
            # 最后保存一次
            if all_notes:
                try:
                    self._save_to_excel(all_notes, keyword)
                    print(f"\n程序结束，共保存 {len(all_notes)} 条数据")
                except Exception as e:
                    print(f"最终保存数据时出错: {e}")
            else:
                print("警告：没有收集到任何数据")
            
            return all_notes

    def _save_to_excel(self, notes, keyword):
        """
        保存数据到Excel
        """
        if not notes:
            print("没有数据需要保存")
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(notes)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.data_path, f"xiaohongshu_{keyword}_{timestamp}.xlsx")
            
            # 保存为Excel
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\n数据已保存到: {filename}")
            print(f"保存的数据条数: {len(df)}")
            
            # 打印保存的数据概要
            print("\n数据概要:")
            print(f"总条数: {len(df)}")
            print(f"包含的字段: {', '.join(df.columns)}")
            
            # 验证文件是否成功创建
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"文件大小: {file_size/1024:.2f} KB")
            else:
                print("警告：文件似乎未成功创建")
            
        except Exception as e:
            print(f"保存到Excel时出错: {e}")
            
            # 尝试保存为CSV作为备选
            try:
                csv_filename = filename.replace('.xlsx', '.csv')
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"已保存为CSV格式: {csv_filename}")
            except Exception as csv_e:
                print(f"保存CSV也失败: {csv_e}")

    def analyze_data(self, df):
        """
        简单的数据分析
        """
        if df is None or df.empty:
            return
            
        print("\n=== 数据分析结果 ===")
        print(f"总笔记数: {len(df)}")
        print(f"平均点赞数: {df['点赞数'].mean():.2f}")
        print(f"平均评论数: {df['评论数'].mean():.2f}")
        print(f"平均收藏数: {df['收藏数'].mean():.2f}")
        
        # 互动率最高的前5篇笔记
        df['互动率'] = df['点赞数'] + df['评论数'] + df['收藏数']
        top_notes = df.nlargest(5, '互动率')
        print("\n互动率最高的5篇笔记：")
        for _, note in top_notes.iterrows():
            print(f"标题: {note['标题']}")
            print(f"用户: {note['用户名']}")
            print(f"互动数: 点赞{note['点赞数']}, 评论{note['评论数']}, 收藏{note['收藏数']}")
            print("---")

if __name__ == "__main__":
    scraper = XiaohongshuScraper()
    keyword = "哈尔滨冰雪大世界自媒体营销策略"
    df = scraper.scrape_and_save(keyword)
    scraper.analyze_data(df) 