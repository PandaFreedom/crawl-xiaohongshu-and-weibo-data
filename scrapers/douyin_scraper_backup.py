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

class DouyinScraper:
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
        self.data_path = os.path.join(os.path.dirname(current_dir), "data", "douyin")
        os.makedirs(self.data_path, exist_ok=True)
        print(f"数据将保存到: {self.data_path}")
        self.is_running = True
        self.paused = False

    def init_driver(self):
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

    def keyboard_listener(self):
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

    def parse_video(self, element):
        try:
            print("\n尝试解析视频数据...")
            
            # 获取标题
            title_selectors = [
                '.title', '.desc', '[data-e2e="video-desc"]', 
                '.video-title', '.video-name', 'h1', 
                '.search-card-title'
            ]
            
            title = "未知标题"
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if title_elem and title_elem.text.strip():
                        title = title_elem.text.strip()
                        break
                except:
                    continue
                    
            if title == "未知标题":
                # 尝试使用XPath
                try:
                    title_elem = element.find_element(By.XPATH, ".//*[contains(@class, 'title') or contains(@class, 'desc')]")
                    title = title_elem.text.strip()
                except:
                    pass
                    
            print(f"标题: {title}")

            # 获取作者
            author_selectors = [
                '.author', '.nickname', '[data-e2e="video-author"]',
                '.user-name', '.creator-name', '.account'
            ]
            
            author = "未知作者"
            for selector in author_selectors:
                try:
                    author_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if author_elem and author_elem.text.strip():
                        author = author_elem.text.strip()
                        break
                except:
                    continue
                    
            if author == "未知作者":
                # 尝试使用XPath
                try:
                    author_elem = element.find_element(By.XPATH, ".//*[contains(@class, 'author') or contains(@class, 'nickname')]")
                    author = author_elem.text.strip()
                except:
                    pass
                    
            print(f"作者: {author}")

            # 获取互动数据
            likes, comments, collects = 0, 0, 0
            
            # 尝试获取所有数字元素
            number_elements = []
            number_selectors = [
                '.number', '.count', '[data-e2e*="like"]', 
                '[data-e2e*="comment"]', '[data-e2e*="collect"]',
                '.statistics span', '.video-data span', '.video-stats'
            ]
            
            for selector in number_selectors:
                try:
                    elems = element.find_elements(By.CSS_SELECTOR, selector)
                    if elems:
                        number_elements.extend(elems)
                except:
                    continue
            
            print(f"找到 {len(number_elements)} 个可能的数字元素")
            
            # 分析数字元素
            for elem in number_elements:
                try:
                    text = elem.text.strip()
                    if not text or not any(c.isdigit() for c in text):
                        continue
                        
                    # 获取父元素HTML用于判断类型
                    parent_html = ""
                    try:
                        parent = elem.find_element(By.XPATH, '..')
                        parent_html = parent.get_attribute('outerHTML').lower()
                    except:
                        parent_html = elem.get_attribute('outerHTML').lower()
                    
                    print(f"数字元素: {text}, 上下文: {parent_html[:50]}...")
                    
                    # 根据上下文判断数据类型
                    if any(word in parent_html for word in ['like', '赞', '点赞', 'digg']):
                        likes = self._convert_count(text)
                        print(f"识别为点赞数: {likes}")
                    elif any(word in parent_html for word in ['comment', '评论', 'reply']):
                        comments = self._convert_count(text)
                        print(f"识别为评论数: {comments}")
                    elif any(word in parent_html for word in ['collect', '收藏', 'favorite', 'star']):
                        collects = self._convert_count(text)
                        print(f"识别为收藏数: {collects}")
                    # 如果无法判断类型但有数字，按顺序赋值
                    elif likes == 0:
                        likes = self._convert_count(text)
                        print(f"默认为点赞数: {likes}")
                    elif comments == 0:
                        comments = self._convert_count(text)
                        print(f"默认为评论数: {comments}")
                    elif collects == 0:
                        collects = self._convert_count(text)
                        print(f"默认为收藏数: {collects}")
                except Exception as e:
                    print(f"处理数字元素时出错: {e}")
                    continue
            
            # 获取发布时间
            publish_date = datetime.now().strftime('%Y-%m-%d')
            time_selectors = [
                '.time', '.date', '[data-e2e="video-create-time"]',
                '.publish-time', '.video-time'
            ]
            
            for selector in time_selectors:
                try:
                    time_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if time_elem and time_elem.text.strip():
                        time_text = time_elem.text.strip()
                        print(f"原始时间文本: {time_text}")
                        
                        # 解析时间
                        if '年' in time_text and '月' in time_text:
                            date = datetime.strptime(time_text, '%Y年%m月%d日')
                            publish_date = date.strftime('%Y-%m-%d')
                        elif '天前' in time_text:
                            days = int(re.search(r'(\d+)', time_text).group(1))
                            date = datetime.now() - timedelta(days=days)
                            publish_date = date.strftime('%Y-%m-%d')
                        elif '小时前' in time_text:
                            hours = int(re.search(r'(\d+)', time_text).group(1))
                            date = datetime.now() - timedelta(hours=hours)
                            publish_date = date.strftime('%Y-%m-%d')
                        elif '分钟前' in time_text:
                            date = datetime.now()
                            publish_date = date.strftime('%Y-%m-%d')
                        
                        print(f"解析后的发布时间: {publish_date}")
                        break
                except:
                    continue

            # 获取视频链接
            link = ""
            try:
                link_elem = element.find_element(By.TAG_NAME, 'a')
                link = link_elem.get_attribute('href')
                print(f"视频链接: {link}")
            except:
                print("未找到视频链接")

            return {
                '标题': title,
                '作者': author,
                '点赞数': likes,
                '评论数': comments,
                '收藏数': collects,
                '发布时间': publish_date,
                '链接': link
            }
            
        except Exception as e:
            print(f"解析视频数据出错: {e}")
            return None

    def _convert_count(self, text):
        """转换互动数据"""
        try:
            text = text.strip()
            if not text:
                return 0
            
            if 'w' in text:
                num = float(text.replace('w', ''))
                return int(num * 10000)
            elif '万' in text:
                num = float(text.replace('万', ''))
                return int(num * 10000)
            else:
                return int(text)
        except:
            return 0

    def scroll_page(self, driver):
        """
        滚动页面加载更多内容
        """
        try:
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                # 滚动到页面底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                
                # 计算新的滚动高度并与上一个滚动高度进行比较
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # 如果高度没有变化，说明已经到底部
                    break
                last_height = new_height
                print("页面滚动中...")
        except Exception as e:
            print(f"滚动页面时出错: {e}")

    def scrape_and_save(self, keyword, max_videos=100):
        driver = self.init_driver()
        all_videos = []
        save_counter = 0
        
        try:
            print("\n开始访问抖音...")
            search_url = f"https://www.douyin.com/search/{keyword}"
            driver.get(search_url)
            
            print("\n请在浏览器中完成登录")
            print("1. 使用手机扫描二维码")
            print("2. 完成可能出现的验证")
            input("\n完成登录后，按回车键继续...")
            
            print(f"\n开始搜索关键词：{keyword}")
            time.sleep(5)  # 等待页面加载
            
            # 检查是否需要切换到视频标签
            try:
                video_tab = driver.find_element(By.XPATH, "//span[contains(text(), '视频') or contains(text(), 'Videos')]")
                video_tab.click()
                print("已切换到视频标签")
                time.sleep(3)
            except:
                print("未找到视频标签或已经在视频标签页")
            
            # 开始滚动和采集
            scroll_count = 0
            max_scroll = 30  # 最大滚动次数，防止无限循环
            
            while len(all_videos) < max_videos and self.is_running and scroll_count < max_scroll:
                # 检查是否暂停
                if self.paused:
                    print("爬虫已暂停，按'p'继续...")
                    time.sleep(1)
                    continue
                
                try:
                    # 获取当前页面上的所有视频元素
                    print("\n尝试获取视频元素...")
                    
                    # 尝试多种可能的选择器
                    selectors = [
                        '.douyin-search-card', 
                        '.search-result-card',
                        '.video-card',
                        '[data-e2e="searchcard-item"]',
                        '.search_card_video'
                    ]
                    
                    video_elements = []
                    for selector in selectors:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            video_elements = elements
                            print(f"使用选择器 '{selector}' 找到 {len(elements)} 个视频元素")
                            break
                    
                    if not video_elements:
                        print("未找到视频元素，尝试使用XPath...")
                        video_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'card') and .//a]")
                        print(f"使用XPath找到 {len(video_elements)} 个视频元素")
                    
                    # 如果仍然没有找到元素，打印页面源码的一部分用于调试
                    if not video_elements:
                        print("\n未找到任何视频元素，打印页面源码片段:")
                        page_source = driver.page_source
                        print(page_source[:1000] + "...")  # 只打印前1000个字符
                    
                    # 处理找到的视频元素
                    for i, element in enumerate(video_elements):
                        if len(all_videos) >= max_videos:
                            break
                        
                        if self.paused:
                            print("爬虫已暂停，按'p'继续...")
                            break
                        
                        try:
                            # 滚动到元素位置确保加载
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(1)
                            
                            # 解析视频数据
                            print(f"\n正在解析第 {i+1} 个视频...")
                            video_data = self.parse_video(element)
                            
                            if video_data:
                                print(f"成功解析视频: {video_data['标题'][:30]}...")
                                all_videos.append(video_data)
                                save_counter += 1
                                
                                # 每解析3个视频保存一次
                                if save_counter >= 3:
                                    if all_videos:
                                        df = pd.DataFrame(all_videos)
                                        self._save_to_excel(df, keyword)
                                        print(f"已保存 {len(all_videos)} 个视频数据")
                                    save_counter = 0
                        except Exception as e:
                            print(f"处理单个视频时出错: {str(e)}")
                            continue
                    
                    # 滚动页面加载更多
                    print("\n滚动页面加载更多视频...")
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # 等待加载
                    
                    # 检查是否已滚动到底部
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        scroll_count += 1
                        print(f"可能已到达页面底部，继续尝试 ({scroll_count}/{max_scroll})")
                    else:
                        scroll_count = 0  # 重置计数器
                    
                except Exception as e:
                    print(f"页面处理出错: {str(e)}")
                    scroll_count += 1
                    time.sleep(2)
            
            print("\n已完成视频采集")
            
        except Exception as e:
            print(f"\n程序出错: {str(e)}")
        
        finally:
            if all_videos:
                df = pd.DataFrame(all_videos)
                self._save_to_excel(df, keyword)
                print(f"\n共采集 {len(all_videos)} 个视频")
                driver.quit()
                return df
            else:
                print("\n警告：没有采集到任何数据")
                driver.quit()
                return pd.DataFrame()

    def _save_to_excel(self, videos, keyword):
        if not videos.empty:
            try:
                df = videos
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.join(self.data_path, f"douyin_{keyword}_{timestamp}.xlsx")
                
                df.to_excel(filename, index=False, engine='openpyxl')
                print(f"\n数据已保存到: {filename}")
                print(f"保存的数据条数: {len(df)}")
                
                print("\n数据概要:")
                print(f"总条数: {len(df)}")
                print(f"包含的字段: {', '.join(df.columns)}")
                
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"文件大小: {file_size/1024:.2f} KB")
                else:
                    print("警告：文件似乎未成功创建")
                
            except Exception as e:
                print(f"保存到Excel时出错: {e}")
                try:
                    csv_filename = filename.replace('.xlsx', '.csv')
                    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                    print(f"已保存为CSV格式: {csv_filename}")
                except Exception as csv_e:
                    print(f"保存CSV也失败: {csv_e}")
        else:
            print("没有数据需要保存")

    def analyze_data(self, df):
        if df.empty:
            print("\n没有数据可供分析")
            return
        
        print("\n" + "="*50)
        print("数据分析报告")
        print("="*50)
        print(f"1. 基础统计")
        print(f"   - 总视频数: {len(df)}个")
        print(f"   - 平均点赞数: {df['点赞数'].mean():.0f}")
        print(f"   - 平均评论数: {df['评论数'].mean():.0f}")
        print(f"   - 平均收藏数: {df['收藏数'].mean():.0f}")
        
        print("\n2. 互动最高的视频 Top5")
        df['互动率'] = df['点赞数'] + df['评论数'] + df['收藏数']
        top_videos = df.nlargest(5, '互动率')
        
        for i, (_, video) in enumerate(top_videos.iterrows(), 1):
            print(f"\n   Top {i}:")
            print(f"   - 标题: {video['标题'][:30]}...")
            print(f"   - 作者: {video['作者']}")
            print(f"   - 互动数据:")
            print(f"     点赞: {video['点赞数']}")
            print(f"     评论: {video['评论数']}")
            print(f"     收藏: {video['收藏数']}")
        
        print("\n" + "="*50)
        print("分析完成")
        print("="*50)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("欢迎使用抖音数据采集程序")
    print("="*60)
    print("\n功能说明:")
    print("1. 本程序可以采集抖音搜索结果中的视频数据")
    print("2. 采集的数据包括：标题、作者、点赞数、评论数、收藏数、发布时间、链接")
    print("3. 数据将保存为Excel格式")
    print("\n操作说明:")
    print("1. 输入关键词和需要采集的视频数量")
    print("2. 程序启动后，请在浏览器中完成登录")
    print("3. 采集过程中可以按'p'键暂停/继续")
    print("4. 采集完成后会自动保存数据并生成分析报告")
    print("="*60)
    
    keyword = input("\n请输入要搜索的关键词: ")
    max_count = input("请输入要采集的视频数量(直接回车默认100个): ")
    
    try:
        max_count = int(max_count) if max_count.strip() else 100
    except:
        print("输入的数量无效，将使用默认值100")
        max_count = 100
    
    scraper = DouyinScraper()
    
    # 启动键盘监听线程
    keyboard_thread = threading.Thread(target=scraper.keyboard_listener)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    
    print("\n" + "="*60)
    print(f"开始采集关键词 '{keyword}' 的视频数据，计划采集 {max_count} 个")
    print("程序运行中可随时按'p'键暂停/继续采集")
    print("="*60)
    
    df = scraper.scrape_and_save(keyword, max_count)
    scraper.is_running = False  # 停止键盘监听线程
    
    if not df.empty:
        print("\n" + "="*60)
        print("数据采集完成，开始生成分析报告...")
        scraper.analyze_data(df)
    
    print("\n" + "="*60)
    print("程序执行完毕")
    print(f"数据已保存到: {scraper.data_path}")
    print("="*60)
    
    input("\n按回车键退出程序...")