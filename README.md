# BTC 交易策略系统

基于技术分析（70%）+ 新闻情绪（30%）的加密货币自动化交易策略指导系统。

## 快速开始

### 1. 安装依赖

**方法一（推荐）：使用 python -m pip**

```powershell
python -m pip install ccxt pandas ta numpy requests
```

**方法二：使用 requirements.txt**

```powershell
python -m pip install -r requirements.txt
```

> ⚠️ 如果提示 `pip` 命令不存在，请使用 `python -m pip` 替代

### 2. 运行策略分析

```powershell
python btc_trading_strategy.py
```

### 3. 按提示输入信息

```
请输入交易对（如 BTC/USDT）: BTC/USDT
请输入总资金（USDT）: 10000
```

## 系统架构

### 核心文件说明

- **btc_trading_strategy.py** - 主策略脚本，执行完整的交易信号分析
- **news_sentiment.py** - 新闻情绪分析模块，从多个来源获取并分析新闻
- **requirements.txt** - Python 依赖包清单
- **虚拟货币交易策略.txt** - 完整的交易规则和策略文档

### 策略逻辑流程

```
用户输入 → K线数据获取 → 新闻情绪分析(30%) → 日线方向判断(70%)
    ↓
4小时支撑/压力位计算 → 1小时入场信号确认 → 仓位与止损止盈计算
    ↓
输出完整交易策略（方向/价格/仓位/止损止盈）
```

## 交易规则要点

### 多周期共振分析
- **日线**：MA60 + MACD 确认大趋势（多头/空头/震荡）
- **4小时**：计算斐波那契38.2%回撤位作为支撑/压力
- **1小时**：反转K线（锤子线/流星线）+ RSI超卖/超买 + 成交量放大

### 风控参数（硬性约束）
```python
单笔止损 ≤ 总资金 1%
趋势行情仓位 ≤ 3%
震荡行情仓位 ≤ 2%
止损位设置在支撑/压力位外侧2%
```

### 新闻情绪分析
- **权重占比**：30%
- **数据来源**：CoinDesk / Cointelegraph / Twitter（当前使用模拟数据）
- **关键词**：降息/加息（权重3）、监管政策（权重2）、名人喊话（权重1.5）
- **时间衰减**：24小时内100%权重，超过后每小时衰减5%

### 严格约束
❌ **禁止市价单** - 所有交易必须使用限价单  
❌ **禁止追单** - 趋势形成后必须等待回撤至关键位  
❌ **禁止逆势** - 日线方向不明时不开单

## 输出示例

```
==================================================
✅ 交易策略建议
==================================================

【开单方向】做多 (LONG)
【入场价格】$90,000.00 (限价单)
【止损价格】$88,200.00 (跌破立即止损)
【止盈目标1】$95,400.00 (平仓50%仓位)
【止盈目标2】$100,800.00 (剩余仓位趋势跟踪)

【仓位管理】
  - 建议仓位比例: 2.50%
  - 开仓金额: $250.00 USDT
  - 购买数量: 0.002778 BTC
  - 最大亏损: $100.00 (总资金的1%)

【策略依据】
  1. 日线多头（价格站稳MA60，MACD柱为正）
  2. 4小时支撑位 $90,000（斐波38.2%回撤）
  3. 1小时锤子线 + RSI超卖(28) + 成交量放大
  4. 新闻情绪：偏向利好（白宫确认不清算BTC）
```

## 配置说明

### 修改交易所API（可选）

如需实盘交易，编辑 `btc_trading_strategy.py`：

```python
# 在 init_exchange() 函数中添加你的API密钥
EXCHANGE = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}  # 现货改为 'spot'
})
```

### 接入真实新闻API（可选）

编辑 `news_sentiment.py`，将 `_get_simulated_news()` 替换为：

```python
# 使用 CryptoCompare 免费API
news_items = fetch_real_news_cryptocompare(crypto_symbol)
```

## 安全提示

⚠️ **默认模式**：脚本仅输出策略建议，**不会自动下单**  
⚠️ **回测优先**：建议先用历史数据回测2周以上  
⚠️ **模拟盘验证**：实盘前至少运行模拟盘1周  
⚠️ **风险自负**：量化交易存在亏损风险，请谨慎操作

## 常见问题

### Q1: 如何修改止损比例？
编辑 `btc_trading_strategy.py` 中的 `TradingConfig.STOP_LOSS_OFFSET`（默认2%）

### Q2: 如何调整新闻权重？
修改 `TradingConfig.NEWS_WEIGHT`（默认0.3，即30%）

### Q3: 支持其他币种吗？
支持，运行时输入任意交易对（如 ETH/USDT、SOL/USDT）

### Q4: 可以自动下单吗？
代码已预留自动下单接口，取消 `generate_trading_strategy()` 末尾的注释即可，**但请务必谨慎测试**

## 技术支持

- 查看完整策略文档：[虚拟货币交易策略.txt](虚拟货币交易策略.txt)
- AI 开发指导：[.github/copilot-instructions.md](.github/copilot-instructions.md)
- 技术指标参考：https://technical-analysis-library-in-python.readthedocs.io/

## 版本历史

- **v1.0** (2026-01-20) - 初始版本，支持BTC多周期分析 + 新闻情绪
