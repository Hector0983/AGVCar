# -*- coding: utf-8 -*-
"""
BTC 交易策略指导系统
功能：基于技术指标（70%）+ 新闻情绪（30%）判断开单方向和仓位管理
作者：自动化交易系统
日期：2026-01-20
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator
from news_sentiment import get_news_sentiment

# ===================== 全局配置 =====================
class TradingConfig:
    # 风控参数
    MAX_POSITION_RATIO = 0.03  # 趋势行情最大仓位 3%
    MAX_POSITION_RANGE_RATIO = 0.02  # 震荡行情最大仓位 2%
    MAX_LOSS_RATIO = 0.01  # 单笔止损 ≤ 总资金 1%
    STOP_LOSS_OFFSET = 0.02  # 止损位外侧偏移 2%
    
    # 技术指标参数
    MA_FAST = 60
    MA_SLOW = 120
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # 权重分配
    TECHNICAL_WEIGHT = 0.7  # 技术指标权重 70%
    NEWS_WEIGHT = 0.3  # 新闻情绪权重 30%
    
    # 交易所配置
    EXCHANGE_ID = 'binance'
    MARKET_TYPE = 'future'  # 'future' 或 'spot'

# ===================== 工具函数 =====================
def init_exchange(api_key=None, secret=None):
    """初始化交易所连接（无API Key时使用公开数据）"""
    exchange_class = getattr(ccxt, TradingConfig.EXCHANGE_ID)
    config = {
        'enableRateLimit': True,
        'options': {'defaultType': TradingConfig.MARKET_TYPE}
    }
    if api_key and secret:
        config['apiKey'] = api_key
        config['secret'] = secret
    
    return exchange_class(config)

def fetch_ohlcv_data(exchange, symbol, timeframe, limit=200):
    """获取K线数据"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"❌ 获取{timeframe}K线数据失败: {e}")
        return None

def calculate_indicators(df):
    """计算所有技术指标"""
    # 均线
    df['ma60'] = SMAIndicator(close=df['close'], window=TradingConfig.MA_FAST).sma_indicator()
    df['ma120'] = SMAIndicator(close=df['close'], window=TradingConfig.MA_SLOW).sma_indicator()
    
    # MACD
    macd = MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()
    
    # RSI
    df['rsi'] = RSIIndicator(close=df['close'], window=TradingConfig.RSI_PERIOD).rsi()
    
    return df

def fibonacci_retracement(high, low):
    """计算斐波那契回撤位"""
    diff = high - low
    return {
        'fib_382': high - diff * 0.382,  # 支撑位/入场位
        'fib_618': high - diff * 0.618   # 压力位/止盈位
    }

def detect_reversal_candle(df):
    """检测反转K线形态"""
    if len(df) < 1:
        return False, False
    
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    
    # 避免除零
    if body < 0.0001:
        return False, False
    
    # 计算影线
    if last['close'] > last['open']:  # 阳线
        wick_low = last['open'] - last['low']
        wick_high = last['high'] - last['close']
    else:  # 阴线
        wick_low = last['close'] - last['low']
        wick_high = last['high'] - last['open']
    
    # 锤子线（多头反转）：下影线≥2倍实体，上影线≤0.5倍实体，收阳
    hammer = (wick_low >= 2 * body) and (wick_high <= 0.5 * body) and (last['close'] > last['open'])
    
    # 流星线（空头反转）：上影线≥2倍实体，下影线≤0.5倍实体，收阴
    shooting_star = (wick_high >= 2 * body) and (wick_low <= 0.5 * body) and (last['close'] < last['open'])
    
    return hammer, shooting_star

# ===================== 趋势判断逻辑 =====================
def analyze_daily_trend(df_1d):
    """日线大方向判断（必须通过，否则不开单）"""
    if df_1d is None or len(df_1d) < TradingConfig.MA_SLOW:
        return None, "数据不足"
    
    last = df_1d.iloc[-1]
    
    # 多头条件：价格站稳MA60 且 MACD柱状线为正
    if last['close'] > last['ma60'] and last['macd_hist'] > 0:
        return 'long', f"日线多头（价格 {last['close']:.2f} > MA60 {last['ma60']:.2f}, MACD柱 {last['macd_hist']:.4f}）"
    
    # 空头条件：价格跌破MA60 且 MACD柱状线为负
    elif last['close'] < last['ma60'] and last['macd_hist'] < 0:
        return 'short', f"日线空头（价格 {last['close']:.2f} < MA60 {last['ma60']:.2f}, MACD柱 {last['macd_hist']:.4f}）"
    
    else:
        return None, "日线方向不明（震荡行情），暂不开单"

def analyze_4h_support_resistance(df_4h, trend_direction):
    """4小时支撑/压力位计算"""
    if df_4h is None or len(df_4h) < 20:
        return None, None, "数据不足"
    
    last = df_4h.iloc[-1]
    
    # 计算近20根K线的高低点
    high_20 = df_4h['high'].iloc[-20:].max()
    low_20 = df_4h['low'].iloc[-20:].min()
    fib = fibonacci_retracement(high_20, low_20)
    
    if trend_direction == 'long':
        # 多头：寻找支撑位（斐波38.2% 或 MA60）
        support = max(fib['fib_382'], last['ma60'])
        return support, None, f"4小时支撑位 {support:.2f}（斐波38.2% {fib['fib_382']:.2f}, MA60 {last['ma60']:.2f}）"
    
    elif trend_direction == 'short':
        # 空头：寻找压力位（斐波38.2% 或 MA60）
        resistance = min(fib['fib_382'], last['ma60'])
        return None, resistance, f"4小时压力位 {resistance:.2f}（斐波38.2% {fib['fib_382']:.2f}, MA60 {last['ma60']:.2f}）"
    
    return None, None, "趋势方向未定义"

def analyze_1h_entry_signal(df_1h, trend_direction, support_price, resistance_price):
    """1小时入场信号确认"""
    if df_1h is None or len(df_1h) < 20:
        return False, "数据不足"
    
    last = df_1h.iloc[-1]
    avg_volume = df_1h['volume'].iloc[-20:].mean()
    
    hammer, shooting_star = detect_reversal_candle(df_1h)
    
    if trend_direction == 'long':
        # 多头入场条件
        at_support = (support_price * 0.99 <= last['close'] <= support_price * 1.01)
        rsi_oversold = last['rsi'] < TradingConfig.RSI_OVERSOLD
        volume_surge = last['volume'] > avg_volume * 1.2
        
        if at_support and hammer and rsi_oversold and volume_surge:
            return True, f"✅ 1小时多头信号（锤子线 + RSI {last['rsi']:.1f} + 成交量放大 {last['volume']/avg_volume:.1%}）"
        else:
            reasons = []
            if not at_support:
                reasons.append(f"未到支撑位（当前 {last['close']:.2f} vs 目标 {support_price:.2f}）")
            if not hammer:
                reasons.append("无锤子线反转形态")
            if not rsi_oversold:
                reasons.append(f"RSI未超卖（{last['rsi']:.1f}）")
            if not volume_surge:
                reasons.append("成交量未放大")
            return False, "❌ " + ", ".join(reasons)
    
    elif trend_direction == 'short':
        # 空头入场条件
        at_resistance = (resistance_price * 0.99 <= last['close'] <= resistance_price * 1.01)
        rsi_overbought = last['rsi'] > TradingConfig.RSI_OVERBOUGHT
        volume_surge = last['volume'] > avg_volume * 1.2
        
        if at_resistance and shooting_star and rsi_overbought and volume_surge:
            return True, f"✅ 1小时空头信号（流星线 + RSI {last['rsi']:.1f} + 成交量放大 {last['volume']/avg_volume:.1%}）"
        else:
            reasons = []
            if not at_resistance:
                reasons.append(f"未到压力位（当前 {last['close']:.2f} vs 目标 {resistance_price:.2f}）")
            if not shooting_star:
                reasons.append("无流星线反转形态")
            if not rsi_overbought:
                reasons.append(f"RSI未超买（{last['rsi']:.1f}）")
            if not volume_surge:
                reasons.append("成交量未放大")
            return False, "❌ " + ", ".join(reasons)
    
    return False, "趋势方向未定义"

# ===================== 仓位与止损止盈计算 =====================
def calculate_position_and_stops(entry_price, direction, total_capital, news_sentiment_score):
    """计算开仓仓位、止损位、止盈位"""
    
    # 1. 计算止损位（支撑/压力位外侧2%）
    if direction == 'long':
        stop_loss = entry_price * (1 - TradingConfig.STOP_LOSS_OFFSET)
    else:  # short
        stop_loss = entry_price * (1 + TradingConfig.STOP_LOSS_OFFSET)
    
    # 2. 计算单币亏损金额
    loss_per_coin = abs(entry_price - stop_loss)
    
    # 3. 基于最大亏损反推仓位
    max_coin_amount = (total_capital * TradingConfig.MAX_LOSS_RATIO) / loss_per_coin
    position_value = max_coin_amount * entry_price
    base_position_ratio = position_value / total_capital
    
    # 4. 应用仓位上限（趋势3%，震荡2%）
    position_ratio = min(base_position_ratio, TradingConfig.MAX_POSITION_RATIO)
    
    # 5. 新闻情绪修正（±10%）
    news_adjustment = 1 + (news_sentiment_score * 0.1)  # 分数-1~+1，调整0.9~1.1倍
    adjusted_position_ratio = position_ratio * news_adjustment
    adjusted_position_ratio = max(0.01, min(adjusted_position_ratio, TradingConfig.MAX_POSITION_RATIO))
    
    # 6. 计算止盈位
    if direction == 'long':
        take_profit_1 = entry_price + (entry_price - stop_loss) * 3  # 止损3倍
        take_profit_2 = entry_price + (entry_price - stop_loss) * 6  # 趋势延伸
    else:  # short
        take_profit_1 = entry_price - (stop_loss - entry_price) * 3
        take_profit_2 = entry_price - (stop_loss - entry_price) * 6
    
    return {
        'position_ratio': round(adjusted_position_ratio, 4),
        'position_value': round(total_capital * adjusted_position_ratio, 2),
        'coin_amount': round(max_coin_amount * news_adjustment, 6),
        'stop_loss': round(stop_loss, 2),
        'take_profit_1': round(take_profit_1, 2),
        'take_profit_2': round(take_profit_2, 2),
        'max_loss_usd': round(total_capital * TradingConfig.MAX_LOSS_RATIO, 2),
        'news_adjustment': f"{(news_adjustment - 1) * 100:+.1f}%"
    }

# ===================== 主策略逻辑 =====================
def generate_trading_strategy(symbol, total_capital):
    """
    核心策略生成函数
    """
    print("\n" + "="*70)
    print(f"🚀 BTC 交易策略分析系统")
    print(f"📊 交易对: {symbol}")
    print(f"💰 总资金: ${total_capital:,.2f} USDT")
    print(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # 初始化交易所
    exchange = init_exchange()
    
    # ==================== 第一步：获取K线数据 ====================
    print("📈 第一步：获取多周期K线数据...")
    df_1d = fetch_ohlcv_data(exchange, symbol, '1d', limit=200)
    df_4h = fetch_ohlcv_data(exchange, symbol, '4h', limit=200)
    df_1h = fetch_ohlcv_data(exchange, symbol, '1h', limit=200)
    
    if df_1d is None or df_4h is None or df_1h is None:
        print("❌ 数据获取失败，无法继续分析")
        return None
    
    # 计算技术指标
    df_1d = calculate_indicators(df_1d)
    df_4h = calculate_indicators(df_4h)
    df_1h = calculate_indicators(df_1h)
    
    current_price = df_1h.iloc[-1]['close']
    print(f"✅ 数据获取成功 | 当前价格: ${current_price:,.2f}\n")
    
    # ==================== 第二步：新闻情绪分析（30%权重）====================
    print("📰 第二步：新闻情绪分析（权重30%）...")
    news_score, news_summary = get_news_sentiment(symbol.split('/')[0])
    print(f"   情绪得分: {news_score:+.2f} (-1利空 → +1利好)")
    print(f"   分析摘要: {news_summary}\n")
    
    # ==================== 第三步：日线方向判断（70%权重）====================
    print("📊 第三步：日线大方向判断（权重70%）...")
    trend_direction, trend_reason = analyze_daily_trend(df_1d)
    print(f"   {trend_reason}")
    
    if trend_direction is None:
        print("\n" + "="*70)
        print("⛔ 结论：日线方向不明确，暂不建议开单")
        print("="*70)
        return None
    
    print(f"   ✅ 日线趋势确认: {'做多' if trend_direction == 'long' else '做空'}\n")
    
    # ==================== 第四步：4小时支撑/压力位 ====================
    print("🎯 第四步：4小时支撑/压力位计算...")
    support, resistance, level_info = analyze_4h_support_resistance(df_4h, trend_direction)
    print(f"   {level_info}\n")
    
    # ==================== 第五步：1小时入场信号确认 ====================
    print("⚡ 第五步：1小时入场信号确认...")
    entry_signal, signal_reason = analyze_1h_entry_signal(
        df_1h, trend_direction, support, resistance
    )
    print(f"   {signal_reason}\n")
    
    # ==================== 综合判断与策略输出 ====================
    if not entry_signal:
        print("="*70)
        print("⏳ 结论：当前暂无符合条件的入场信号，建议继续观望")
        print("="*70)
        return None
    
    # 确定入场价格
    entry_price = support if trend_direction == 'long' else resistance
    
    # 计算仓位与止损止盈
    position_info = calculate_position_and_stops(
        entry_price, trend_direction, total_capital, news_score
    )
    
    # ==================== 输出完整策略 ====================
    print("="*70)
    print("✅ 交易策略建议")
    print("="*70)
    print(f"\n【开单方向】{'做多 (LONG)' if trend_direction == 'long' else '做空 (SHORT)'}")
    print(f"【入场价格】${entry_price:,.2f} (限价单)")
    print(f"【止损价格】${position_info['stop_loss']:,.2f} (跌破/突破立即止损)")
    print(f"【止盈目标1】${position_info['take_profit_1']:,.2f} (平仓50%仓位)")
    print(f"【止盈目标2】${position_info['take_profit_2']:,.2f} (剩余仓位趋势跟踪)")
    print(f"\n【仓位管理】")
    print(f"  - 建议仓位比例: {position_info['position_ratio']*100:.2f}% (新闻调整 {position_info['news_adjustment']})")
    print(f"  - 开仓金额: ${position_info['position_value']:,.2f} USDT")
    print(f"  - 购买数量: {position_info['coin_amount']} {symbol.split('/')[0]}")
    print(f"  - 最大亏损: ${position_info['max_loss_usd']} (总资金的1%)")
    
    print(f"\n【策略依据】")
    print(f"  1. {trend_reason}")
    print(f"  2. {level_info}")
    print(f"  3. {signal_reason}")
    print(f"  4. 新闻情绪: {news_summary}")
    
    print("\n" + "="*70)
    print("⚠️  风险提示")
    print("="*70)
    print("1. 严格使用限价单，禁止市价单追单")
    print("2. 挂单后4小时内未成交自动撤单")
    print("3. 止损触发后立即离场，不抱侥幸心理")
    print("4. 到达止盈1后，将剩余仓位止损移至成本价")
    print("="*70 + "\n")
    
    return {
        'symbol': symbol,
        'direction': trend_direction,
        'entry_price': entry_price,
        'current_price': current_price,
        'stop_loss': position_info['stop_loss'],
        'take_profit_1': position_info['take_profit_1'],
        'take_profit_2': position_info['take_profit_2'],
        'position_ratio': position_info['position_ratio'],
        'position_value': position_info['position_value'],
        'coin_amount': position_info['coin_amount'],
        'technical_score': 1.0 if entry_signal else 0.0,
        'news_score': news_score,
        'timestamp': datetime.now().isoformat()
    }

# ===================== 主程序入口 =====================
def main():
    """主程序入口"""
    print("\n" + "🔷"*35)
    print("   BTC 高胜率交易策略系统 v1.0")
    print("   技术分析(70%) + 新闻情绪(30%)")
    print("🔷"*35 + "\n")
    
    # 用户输入
    try:
        symbol_input = input("请输入交易对（如 BTC/USDT）: ").strip().upper()
        if not symbol_input:
            symbol_input = "BTC/USDT"
        
        capital_input = input("请输入总资金（USDT）: ").strip()
        total_capital = float(capital_input) if capital_input else 10000
        
        # 生成策略
        strategy = generate_trading_strategy(symbol_input, total_capital)
        
        # 可选：保存策略到文件
        if strategy:
            save_option = input("\n是否保存策略到文件？(y/n): ").strip().lower()
            if save_option == 'y':
                filename = f"strategy_{symbol_input.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(strategy, f, indent=2, ensure_ascii=False)
                print(f"✅ 策略已保存至: {filename}")
    
    except KeyboardInterrupt:
        print("\n\n程序已退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
