# 快速使用指南

## 第一次使用（3分钟上手）

### 步骤1：安装依赖包

打开 PowerShell，进入项目目录：

```powershell
cd C:\Users\user09\Desktop\python
python -m pip install ccxt pandas ta numpy requests
```

> 💡 **提示**：如果 `pip` 命令无法识别，请使用 `python -m pip` 代替

### 步骤2：运行策略脚本

```powershell
python btc_trading_strategy.py
```

### 步骤3：输入参数

```
请输入交易对（如 BTC/USDT）: BTC/USDT    [直接回车使用默认值]
请输入总资金（USDT）: 10000              [输入你的资金金额]
```

### 步骤4：查看结果

脚本会自动分析并输出：
- ✅ 是否建议开单
- 📊 开多还是开空
- 💰 建议仓位和金额
- 🎯 止损止盈价格
- 📰 新闻情绪分析

## 典型输出解读

```
✅ 交易策略建议
==================================================

【开单方向】做多 (LONG)              ← 买入BTC
【入场价格】$90,000.00               ← 挂限价单在这个价格
【止损价格】$88,200.00               ← 跌破这个价格立即止损
【止盈目标1】$95,400.00              ← 到达后平仓50%
【止盈目标2】$100,800.00             ← 剩余仓位目标价

【仓位管理】
  - 建议仓位比例: 2.50%              ← 占总资金2.5%
  - 开仓金额: $250.00 USDT           ← 投入250美元
  - 购买数量: 0.002778 BTC           ← 买入数量
  - 最大亏损: $100.00                ← 止损后最多亏100美元
```

## 重要提醒

### ⚠️ 脚本不会自动下单
- 当前版本仅**输出策略建议**
- 你需要**手动**在交易所执行
- 这样更安全，避免程序误操作

### ✅ 如何在币安手动执行

1. 登录币安交易所
2. 选择 BTC/USDT 交易对
3. 点击"限价委托"
4. 输入脚本建议的价格和数量
5. 同时设置止损止盈单（OCO单）

### 📊 建议的操作流程

```
运行脚本 → 查看分析结果 → 判断是否采纳 → 手动下单 → 保存策略记录
```

## 高级功能

### 保存策略到文件

运行结束时选择 `y`：

```
是否保存策略到文件？(y/n): y
✅ 策略已保存至: strategy_BTC_USDT_20260120_143052.json
```

### 修改风控参数

编辑 `btc_trading_strategy.py`，找到 `TradingConfig` 类：

```python
class TradingConfig:
    MAX_POSITION_RATIO = 0.03      # 改为 0.05 = 最大仓位5%
    MAX_LOSS_RATIO = 0.01          # 改为 0.02 = 最大止损2%
    STOP_LOSS_OFFSET = 0.02        # 改为 0.03 = 止损位3%外侧
```

### 启用真实新闻API

编辑 `news_sentiment.py`，替换第83行：

```python
# 原代码（模拟数据）
news_items = _get_simulated_news(crypto_symbol)

# 改为（真实API）
news_items = fetch_real_news_cryptocompare(crypto_symbol)
```

## 常见错误处理

### 错误1：pip 命令无法识别

```
pip : 无法将"pip"项识别为 cmdlet、函数、脚本文件...
```

**解决方案**：使用 `python -m pip` 替代

```powershell
python -m pip install ccxt pandas ta numpy requests
```

### 错误2：找不到模块 'ccxt' 或 'ta'

```powershell
python -m pip install ccxt
python -m pip install ta
```

### 错误3：网络超时

```python
# 使用代理或检查网络连接
# 或使用离线数据（下载历史K线CSV文件）
```

### 错误4：数据不足

```
日线方向不明（震荡行情），暂不开单
```
→ 这是正常的风控逻辑，表示当前不适合开单

## 进阶学习

### 了解技术指标
- MA60/MA120：60日和120日移动平均线
- MACD：趋势指标，柱状线方向代表动能
- RSI：相对强弱指数，<30超卖，>70超买
- 斐波那契38.2%：常见回撤支撑位

### 了解K线形态
- **锤子线**：下影线长，表明多头反击
- **流星线**：上影线长，表明空头打压

### 查看完整策略文档
打开 `虚拟货币交易策略.txt` 查看详细交易规则

## 测试建议

### 新手推荐流程

1. **模拟运行** - 先运行脚本观察1周，不实际下单
2. **小额测试** - 用100 USDT小额跟单，验证策略
3. **记录复盘** - 每笔交易记录结果，总结经验
4. **逐步加仓** - 策略稳定后再增加资金

### 回测验证（可选）

收集历史K线数据，修改脚本读取CSV文件而非实时API，验证策略历史胜率。

## 获取帮助

- 查看AI开发指导：`.github/copilot-instructions.md`
- 技术指标库文档：https://technical-analysis-library-in-python.readthedocs.io/
- CCXT文档：https://docs.ccxt.com/
