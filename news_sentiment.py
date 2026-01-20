# -*- coding: utf-8 -*-
"""
新闻情绪分析模块
功能：爬取 CoinDesk/Cointelegraph/Twitter 等新闻源，分析加密货币相关新闻情绪
权重：占总交易信号的 30%
"""

import requests
from datetime import datetime, timedelta
import re

class NewsConfig:
    """新闻源配置"""
    # 关键词权重配置
    KEYWORDS = {
        '利好': {
            '降息': 3, 'rate cut': 3, 'interest rate cut': 3,
            '减息': 3, 'dovish': 2, 'easing': 2,
            '增持': 2, 'buying': 2, 'bullish': 2,
            '利好': 2, 'positive': 1, 'optimistic': 1,
            '突破': 1, 'breakout': 1, 'rally': 1,
            '上涨': 1, 'surge': 1, 'pump': 1,
            '采用': 2, 'adoption': 2, 'approved': 2,
            'etf通过': 3, 'etf approved': 3,
            '不会清算': 2, 'not liquidate': 2, 'hold': 1
        },
        '利空': {
            '加息': -3, 'rate hike': -3, 'interest rate hike': -3,
            '升息': -3, 'hawkish': -2, 'tightening': -2,
            '抛售': -2, 'selling': -2, 'bearish': -2,
            '利空': -2, 'negative': -1, 'pessimistic': -1,
            '暴跌': -2, 'crash': -2, 'dump': -2,
            '下跌': -1, 'drop': -1, 'fall': -1,
            '监管': -2, 'regulation': -2, 'ban': -3,
            '清算': -3, 'liquidate': -3, 'liquidation': -3,
            '担忧': -1, 'concern': -1, 'worry': -1
        },
        '名人': {
            '特朗普': 1.5, 'trump': 1.5,
            '马斯克': 1.5, 'musk': 1.5, 'elon': 1.5,
            '美联储': 2.0, 'federal reserve': 2.0, 'fed': 2.0,
            '鲍威尔': 1.5, 'powell': 1.5
        }
    }
    
    # 时间衰减系数（24小时内100%，超过24小时每小时衰减5%）
    TIME_DECAY_HOURS = 24
    TIME_DECAY_RATE = 0.05

def get_news_sentiment(crypto_symbol='BTC'):
    """
    获取并分析新闻情绪
    
    参数:
        crypto_symbol: 加密货币代码，如 'BTC', 'ETH'
    
    返回:
        sentiment_score: 情绪得分 (-1 到 +1)
        summary: 情绪分析摘要
    """
    
    # ==================== 模拟新闻数据（实际使用时替换为真实API）====================
    # 由于真实API需要密钥且有调用限制，这里使用模拟数据展示逻辑
    # 实际使用时可接入：
    # 1. CoinDesk API: https://www.coindesk.com/api/
    # 2. CryptoCompare News API: https://min-api.cryptocompare.com/
    # 3. Twitter API v2: 搜索加密货币相关推文
    
    news_items = fetch_real_news_cryptocompare(crypto_symbol)
    
    if not news_items:
        return 0, "无可用新闻数据，情绪中性"
    
    # ==================== 计算综合情绪得分 ====================
    total_score = 0
    total_weight = 0
    news_details = []
    
    for news in news_items:
        title = news['title'].lower()
        published_time = news['published_at']
        
        # 计算时间衰减系数
        time_decay = _calculate_time_decay(published_time)
        
        # 匹配关键词并计算得分
        sentiment = 0
        matched_keywords = []
        
        # 利好关键词
        for keyword, score in NewsConfig.KEYWORDS['利好'].items():
            if keyword.lower() in title:
                sentiment += score
                matched_keywords.append(f"+{keyword}")
        
        # 利空关键词
        for keyword, score in NewsConfig.KEYWORDS['利空'].items():
            if keyword.lower() in title:
                sentiment += score  # score已经是负数
                matched_keywords.append(f"-{keyword}")
        
        # 名人加权
        celebrity_multiplier = 1.0
        for name, multiplier in NewsConfig.KEYWORDS['名人'].items():
            if name.lower() in title:
                celebrity_multiplier = max(celebrity_multiplier, multiplier)
                matched_keywords.append(f"🔥{name}")
        
        # 应用名人加权和时间衰减
        weighted_sentiment = sentiment * celebrity_multiplier * time_decay
        
        total_score += weighted_sentiment
        total_weight += time_decay
        
        if matched_keywords:
            news_details.append({
                'title': news['title'][:50] + '...',
                'sentiment': weighted_sentiment,
                'keywords': matched_keywords,
                'time_ago': _format_time_ago(published_time)
            })
    
    # 归一化到 -1 ~ +1
    if total_weight > 0:
        normalized_score = max(-1, min(1, total_score / (total_weight * 5)))  # 除以5是为了调节幅度
    else:
        normalized_score = 0
    
    # ==================== 生成摘要 ====================
    summary = _generate_summary(normalized_score, news_details)
    
    return normalized_score, summary

def _get_simulated_news(crypto_symbol):
    """
    模拟新闻数据（实际使用时替换为真实API调用）
    
    真实API示例代码：
    ```python
    # CryptoCompare News API
    url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={crypto_symbol}"
    response = requests.get(url)
    news_data = response.json()['Data']
    ```
    """
    
    # 模拟当前时间附近的新闻（基于2026年1月20日的真实背景）
    now = datetime.now()
    
    simulated_news = [
        {
            'title': '白宫确认：被没收的比特币不会被清算，增强长期信心',
            'published_at': now - timedelta(hours=8),
            'source': 'CoinDesk'
        },
        {
            'title': '币安上线零费用BTC交易对，交易量或大幅提升',
            'published_at': now - timedelta(hours=2),
            'source': 'Binance Announcement'
        },
        {
            'title': '社区担忧：全球宏观紧张局势影响加密货币市场',
            'published_at': now - timedelta(hours=5),
            'source': 'Cointelegraph'
        },
        {
            'title': '美联储鲍威尔：维持利率不变，暂无降息计划',
            'published_at': now - timedelta(hours=12),
            'source': 'Federal Reserve'
        },
        {
            'title': '特朗普：支持美国成为加密货币创新中心',
            'published_at': now - timedelta(hours=18),
            'source': 'Twitter'
        }
    ]
    
    return simulated_news

def _calculate_time_decay(published_time):
    """计算时间衰减系数"""
    hours_ago = (datetime.now() - published_time).total_seconds() / 3600
    
    if hours_ago <= NewsConfig.TIME_DECAY_HOURS:
        return 1.0  # 24小时内权重100%
    else:
        # 超过24小时，每小时衰减5%
        excess_hours = hours_ago - NewsConfig.TIME_DECAY_HOURS
        decay = 1.0 - (excess_hours * NewsConfig.TIME_DECAY_RATE)
        return max(0, decay)  # 不低于0

def _format_time_ago(published_time):
    """格式化发布时间"""
    delta = datetime.now() - published_time
    hours = delta.total_seconds() / 3600
    
    if hours < 1:
        return f"{int(delta.total_seconds() / 60)}分钟前"
    elif hours < 24:
        return f"{int(hours)}小时前"
    else:
        return f"{int(hours / 24)}天前"

def _generate_summary(score, news_details):
    """生成情绪摘要"""
    if score > 0.5:
        sentiment_label = "强烈利好 🚀"
    elif score > 0.2:
        sentiment_label = "偏向利好 📈"
    elif score > -0.2:
        sentiment_label = "中性震荡 ⚖️"
    elif score > -0.5:
        sentiment_label = "偏向利空 📉"
    else:
        sentiment_label = "强烈利空 ⚠️"
    
    # 取最重要的3条新闻
    top_news = sorted(news_details, key=lambda x: abs(x['sentiment']), reverse=True)[:3]
    
    summary_parts = [sentiment_label]
    for news in top_news:
        keywords_str = ' '.join(news['keywords'])
        summary_parts.append(f"   - {news['title']} ({news['time_ago']}) [{keywords_str}]")
    
    return '\n'.join(summary_parts)

# ==================== 真实API集成示例（可选）====================
def fetch_real_news_coindesk(crypto_symbol='BTC'):
    """
    示例：从 CoinDesk 获取真实新闻（需要根据实际API文档调整）
    
    注意：CoinDesk 公开API可能需要注册或有调用限制
    """
    try:
        # 示例URL（实际使用时需验证）
        url = "https://www.coindesk.com/arc/outboundfeeds/news/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 解析RSS/JSON（根据实际返回格式）
            # 这里仅为示例框架
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            news_items = []
            for item in root.findall('.//item')[:10]:
                news_items.append({
                    'title': item.find('title').text,
                    'published_at': datetime.now(),  # 需解析实际时间
                    'source': 'CoinDesk'
                })
            
            return news_items
        else:
            print(f"⚠️  CoinDesk API调用失败: {response.status_code}")
            return []
    
    except Exception as e:
        print(f"⚠️  获取真实新闻失败: {e}")
        return []

def fetch_real_news_cryptocompare(crypto_symbol='BTC'):
    """
    示例：从 CryptoCompare 获取新闻（免费API，推荐）
    
    API文档：https://min-api.cryptocompare.com/documentation
    """
    try:
        url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories={crypto_symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            news_items = []
            
            for item in data.get('Data', [])[:10]:
                published_timestamp = item.get('published_on', 0)
                news_items.append({
                    'title': item.get('title', ''),
                    'published_at': datetime.fromtimestamp(published_timestamp),
                    'source': item.get('source', 'Unknown')
                })
            
            return news_items
        else:
            print(f"⚠️  CryptoCompare API调用失败: {response.status_code}")
            return []
    
    except Exception as e:
        print(f"⚠️  获取CryptoCompare新闻失败: {e}")
        return []

# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("测试新闻情绪分析模块...\n")
    
    score, summary = get_news_sentiment('BTC')
    
    print(f"情绪得分: {score:+.2f}")
    print(f"分析摘要:\n{summary}")
    
    # # 测试真实API（需要网络连接）
    # real_news = fetch_real_news_cryptocompare('BTC')
    # print(f"\n获取到 {len(real_news)} 条真实新闻")
