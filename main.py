from scrapers.xiaohongshu_scraper import XiaohongshuScraper
from scrapers.weibo_scraper import WeiboScraper
from scrapers.douyin_scraper import DouyinScraper
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import jieba
import jieba.analyse
from collections import Counter
import numpy as np

class SocialMediaAnalyzer:
    def __init__(self):
        self.xhs_scraper = XiaohongshuScraper()
        self.weibo_scraper = WeiboScraper()
        self.douyin_scraper = DouyinScraper()
        self.results_path = "results"
        os.makedirs(self.results_path, exist_ok=True)

    def scrape_all_platforms(self, keyword):
        """
        爬取所有平台的数据
        """
        print("开始爬取小红书数据...")
        xhs_df = self.xhs_scraper.scrape_and_save(keyword)
        
        print("\n开始爬取微博数据...")
        weibo_df = self.weibo_scraper.scrape_and_save(keyword)
        
        print("\n开始爬取抖音数据...")
        douyin_df = self.douyin_scraper.scrape_and_save(keyword)
        
        return xhs_df, weibo_df, douyin_df

    def analyze_engagement(self, xhs_df, weibo_df, douyin_df):
        """
        分析各平台互动数据
        """
        print("\n=== 平台互动数据分析 ===")
        
        # 计算平均互动率
        platform_stats = []
        
        if xhs_df is not None and not xhs_df.empty:
            xhs_stats = {
                '平台': '小红书',
                '内容数量': len(xhs_df),
                '平均点赞': xhs_df['likes'].mean(),
                '平均评论': xhs_df['comments'].mean(),
                '平均收藏': xhs_df['collects'].mean() if 'collects' in xhs_df.columns else 0
            }
            platform_stats.append(xhs_stats)
            
        if weibo_df is not None and not weibo_df.empty:
            weibo_stats = {
                '平台': '微博',
                '内容数量': len(weibo_df),
                '平均点赞': weibo_df['attitudes_count'].mean(),
                '平均评论': weibo_df['comments_count'].mean(),
                '平均转发': weibo_df['reposts_count'].mean()
            }
            platform_stats.append(weibo_stats)
            
        if douyin_df is not None and not douyin_df.empty:
            douyin_stats = {
                '平台': '抖音',
                '内容数量': len(douyin_df),
                '平均点赞': douyin_df['likes'].mean(),
                '平均评论': douyin_df['comments'].mean(),
                '平均分享': douyin_df['shares'].mean()
            }
            platform_stats.append(douyin_stats)
        
        # 创建数据框
        stats_df = pd.DataFrame(platform_stats)
        
        # 保存统计结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stats_df.to_csv(f"{self.results_path}/platform_stats_{timestamp}.csv", 
                       index=False, encoding='utf-8-sig')
        
        # 绘制互动数据对比图
        self.plot_engagement_comparison(stats_df)
        
        return stats_df

    def plot_engagement_comparison(self, stats_df):
        """
        绘制互动数据对比图
        """
        plt.figure(figsize=(12, 6))
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 准备数据
        metrics = ['平均点赞', '平均评论']
        x = np.arange(len(stats_df['平台']))
        width = 0.35
        
        # 绘制柱状图
        for i, metric in enumerate(metrics):
            plt.bar(x + i*width, stats_df[metric], width, label=metric)
        
        plt.xlabel('平台')
        plt.ylabel('数量')
        plt.title('各平台互动数据对比')
        plt.xticks(x + width/2, stats_df['平台'])
        plt.legend()
        
        # 保存图表
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plt.savefig(f"{self.results_path}/engagement_comparison_{timestamp}.png")
        plt.close()

    def analyze_content(self, xhs_df, weibo_df, douyin_df):
        """
        分析内容主题和关键词
        """
        print("\n=== 内容主题分析 ===")
        
        all_content = []
        
        # 收集所有文本内容
        if xhs_df is not None and not xhs_df.empty:
            all_content.extend(xhs_df['title'].tolist())
            all_content.extend(xhs_df['desc'].tolist())
            
        if weibo_df is not None and not weibo_df.empty:
            all_content.extend(weibo_df['content'].tolist())
            
        if douyin_df is not None and not douyin_df.empty:
            all_content.extend(douyin_df['title'].tolist())
        
        # 提取关键词
        text = ' '.join([str(content) for content in all_content if pd.notna(content)])
        keywords = jieba.analyse.extract_tags(text, topK=20, withWeight=True)
        
        # 打印关键词
        print("\n热门关键词及权重：")
        for keyword, weight in keywords:
            print(f"{keyword}: {weight:.4f}")
        
        # 保存关键词分析结果
        keywords_df = pd.DataFrame(keywords, columns=['keyword', 'weight'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        keywords_df.to_csv(f"{self.results_path}/keywords_analysis_{timestamp}.csv", 
                          index=False, encoding='utf-8-sig')
        
        # 绘制词云图
        self.plot_word_cloud(dict(keywords))

    def plot_word_cloud(self, keywords_dict):
        """
        绘制词云图
        """
        from wordcloud import WordCloud
        
        # 生成词云
        wc = WordCloud(
            font_path='SimHei',  # 使用中文字体
            width=800,
            height=400,
            background_color='white'
        )
        
        wc.generate_from_frequencies(keywords_dict)
        
        # 保存词云图
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        wc.to_file(f"{self.results_path}/wordcloud_{timestamp}.png")

    def generate_report(self, stats_df, keyword):
        """
        生成分析报告
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"{self.results_path}/analysis_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 哈尔滨冰雪大世界自媒体营销分析报告\n\n")
            f.write(f"## 1. 数据概览\n\n")
            
            # 写入各平台数据统计
            f.write("### 1.1 平台数据统计\n\n")
            f.write(stats_df.to_markdown())
            f.write("\n\n")
            
            # 写入分析结论
            f.write("## 2. 分析结论\n\n")
            
            # 计算总体参与度
            total_engagement = stats_df.iloc[:, 2:].sum().sum()
            f.write(f"### 2.1 总体参与度\n")
            f.write(f"- 总互动量：{total_engagement:.0f}\n")
            
            # 平台表现对比
            f.write("\n### 2.2 平台表现对比\n")
            for _, row in stats_df.iterrows():
                platform = row['平台']
                content_count = row['内容数量']
                avg_likes = row['平均点赞']
                f.write(f"- {platform}：发布内容 {content_count:.0f} 条，平均获赞 {avg_likes:.0f}\n")
            
            # 写入建议
            f.write("\n## 3. 营销建议\n\n")
            f.write("1. 内容策略优化\n")
            f.write("   - 根据数据分析结果，建议在互动率最高的平台加大内容投放\n")
            f.write("   - 关注高互动内容的共同特点，复制成功经验\n\n")
            
            f.write("2. 平台运营建议\n")
            f.write("   - 针对不同平台特点，制定差异化的内容策略\n")
            f.write("   - 重点关注用户评论，及时互动提升粘性\n\n")
            
            f.write("3. 持续优化方向\n")
            f.write("   - 定期追踪数据变化，及时调整运营策略\n")
            f.write("   - 建立内容质量评估体系，提升内容产出效率\n")

        print(f"\n分析报告已生成：{report_file}")

def main():
    keyword = "哈尔滨冰雪大世界"
    analyzer = SocialMediaAnalyzer()
    
    # 爬取数据
    xhs_df, weibo_df, douyin_df = analyzer.scrape_all_platforms(keyword)
    
    # 分析互动数据
    stats_df = analyzer.analyze_engagement(xhs_df, weibo_df, douyin_df)
    
    # 分析内容
    analyzer.analyze_content(xhs_df, weibo_df, douyin_df)
    
    # 生成报告
    analyzer.generate_report(stats_df, keyword)

if __name__ == "__main__":
    main() 