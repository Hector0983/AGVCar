# Copilot Instructions - 加密货币交易策略系统

## 项目概述
本项目是一个基于技术分析的加密货币（BTC为主）自动化交易策略系统,集成了多时间周期分析、风险管理和新闻情绪分析。

## 核心交易策略框架

### 多维度信号综合判断（100%权重分配）
- **技术指标分析（70%）**：日线 MA60/MA120 + MACD 趋势确认，4小时周期支撑/压力位，1小时反转K线 + RSI + 成交量共振
- **新闻情绪分析（30%）**：美联储政策（降息/加息）、重大监管消息、关键人物喊话（特朗普/马斯克）

### 周期共振逻辑
```
日线定方向 → 4小时判趋势+找支撑压力 → 1小时确认入场信号
```
- 日线：价格与 MA60 位置关系 + MACD柱状线方向
- 4小时：斐波那契38.2%回撤位 + 前高/前低
- 1小时：锤子线/流星线 + RSI超卖(<30)/超买(>70) + 成交量放大

## 编码约定

### 技术指标计算标准
```python
# 使用 ta 库统一计算指标
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator

# MA 默认周期：60/120
# RSI 默认周期：14
# 斐波那契回撤使用：38.2% (支撑/入场), 61.8% (压力/止盈)
```

### K线形态识别规则
- **锤子线（多头反转）**：下影线 ≥ 2倍实体 && 上影线 ≤ 0.5倍实体 && 收盘>开盘
- **流星线（空头反转）**：上影线 ≥ 2倍实体 && 下影线 ≤ 0.5倍实体 && 收盘<开盘

### 风控参数（硬性约束）
```python
MAX_POSITION_RATIO = 0.03  # 趋势行情最大仓位 3%
MAX_POSITION_RANGE_RATIO = 0.02  # 震荡行情最大仓位 2%
MAX_LOSS_RATIO = 0.01  # 单笔止损 ≤ 总资金 1%
STOP_LOSS_OFFSET = 0.02  # 止损位外侧偏移 2%
```

## 关键开发规范

### 1. 开单信号输出格式
交易信号必须包含完整字段：
```python
{
    'direction': 'long' | 'short',
    'entry_price': float,  # 限价单价格
    'stop_loss': float,  # 止损位
    'take_profit_1': float,  # 第一目标（平仓50%）
    'take_profit_2': float,  # 趋势延伸目标
    'position_ratio': float,  # 仓位占比
    'reason': str  # 信号触发原因（含技术+新闻）
}
```

### 2. 新闻情绪分析集成
- 使用 API 或爬虫获取实时新闻（推荐源：CoinDesk、Cointelegraph、Twitter）
- 关键词匹配优先级：降息/加息 > 监管政策 > 名人喊话
- 情绪评分：利好 +1 / 中性 0 / 利空 -1，按时间衰减（24小时内权重100%）

### 3. 仓位动态计算逻辑
```python
# 止损空间越大，仓位越小，确保单笔亏损不超标
loss_per_coin = abs(entry_price - stop_loss_price)
max_coin = (TOTAL_CAPITAL * MAX_LOSS_RATIO) / loss_per_coin
position_ratio = (max_coin * entry_price) / TOTAL_CAPITAL
position_ratio = min(position_ratio, MAX_POSITION_RATIO)  # 上限约束
```

### 4. 禁止事项
- ❌ 严禁使用市价单（`create_market_order`），所有交易必须用限价单
- ❌ 趋势已形成后禁止追单，必须等待回落/反弹至关键位
- ❌ 无明确日线方向时禁止开单，防止震荡行情频繁止损

## 数据源配置

### 交易所API（生产环境）
```python
# 推荐 ccxt 库，支持 Binance/OKX/Coinbase
EXCHANGE = ccxt.binance({
    'apiKey': 'YOUR_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}  # 或 'spot'
})
```

### 回测/模拟模式
- 使用公开K线数据（无需API Key）
- 默认输出信号但不下单，需人工确认后执行

## 工作流程

### 脚本执行标准流程
1. **输入参数**：交易对（如 BTC/USDT）、总资金（USDT）
2. **数据获取**：日线/4小时/1小时K线 + 近24小时新闻
3. **信号判断**：
   - 日线方向过滤（不符合直接退出）
   - 4小时支撑/压力计算
   - 1小时入场信号确认（K线+RSI+成交量）
   - 新闻情绪修正（调整仓位±10%或信号强度）
4. **输出策略**：开单建议/方向/仓位/止损止盈/理由

### 测试与验证
- 回测模式：至少覆盖2周历史数据，验证信号胜率
- 模拟盘：在实时环境测试1周后再考虑实盘
- 记录每笔交易（入场时间/价格/仓位/止损止盈/结果），用于策略迭代

## 外部依赖
```
ccxt>=4.0.0  # 交易所API统一接口
pandas>=2.0.0  # 数据处理
ta>=0.11.0  # 技术指标库
numpy>=1.24.0  # 数值计算
requests>=2.31.0  # 新闻API调用
```

## 参考资料
- [虚拟货币交易策略.txt](虚拟货币交易策略.txt)：完整交易规则、开单计划表、Python代码框架
- 斐波那契回撤位文档：https://www.investopedia.com/terms/f/fibonacciretracement.asp
