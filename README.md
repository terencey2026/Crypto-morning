# 🔥 Crypto Morning Briefing

每日 7:30 自动生成加密货币与概念股晨会速递，推送至飞书 + Web Dashboard。

## 功能

- **加密货币行情**：BTC, ETH, SOL, BNB, UNI, LINK, HYPE, ZEC（CoinGecko API）
- **加密概念股行情**：COIN, HOOD, CRCL, MSTR 等美股（Yahoo Finance）
- **重大新闻聚合**：CryptoPanic 重要新闻 + 情绪标签
- **AI 智能分析**：Gemini API + Google Search 实时搜索，生成【观点—逻辑—标的】
- **飞书推送**：Interactive Card 格式，手机直接阅读
- **Web Dashboard**：暗色主题、移动端优先、历史归档

## 快速部署（15 分钟）

### 第一步：Fork 仓库

1. 点击本仓库右上角 **Fork** 按钮
2. 在你的 GitHub 账号下创建副本

### 第二步：获取 API Keys

| Key | 获取方式 |
|-----|---------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) → Get API Key |
| `FEISHU_WEBHOOK_URL` | 飞书 → 建群 → 群设置 → 机器人 → 添加自定义机器人 → 复制 Webhook |

### 第三步：配置 GitHub Secrets

1. 打开你 Fork 的仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**，逐个添加：
   - Name: `GEMINI_API_KEY`，Value: 你的 Gemini API Key
   - Name: `FEISHU_WEBHOOK_URL`，Value: 你的飞书 Webhook URL

### 第四步：启用 GitHub Pages

1. 仓库 → **Settings** → **Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 **main**，目录选择 **/docs**
4. 点击 Save

你的 Dashboard 地址将是：`https://你的用户名.github.io/crypto-briefing/`

### 第五步：启用 GitHub Actions

1. 仓库 → **Actions** 标签页
2. 如果提示 "Workflows aren't being run"，点击 **I understand my workflows, go ahead and enable them**
3. 点击左侧 **Daily Crypto Briefing** → 右上角 **Run workflow** → **Run workflow** 手动触发一次测试

## 手动触发

在仓库的 **Actions** 页面，选择 **Daily Crypto Briefing**，点击 **Run workflow** 即可手动执行。

## 自定义标的

编辑 `scripts/config.py` 文件即可修改关注的加密货币和股票列表。

### 添加加密货币

```python
CRYPTO_WATCHLIST = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"},
    # 添加新的代币（id 从 CoinGecko 网站获取）：
    {"id": "avalanche-2", "symbol": "AVAX", "name": "Avalanche"},
]
```

### 添加/修改股票

```python
STOCK_WATCHLIST = {
    "primary": [
        {"ticker": "COIN", "name": "Coinbase", "group": "业务类"},
        # 添加新股票：
        {"ticker": "SQ",   "name": "Block",    "group": "业务类"},
    ],
    "secondary": [
        # 次要标的只在涨跌 > 5% 时显示
        {"ticker": "IREN", "name": "Iris Energy", "group": "矿股"},
    ],
}
```

## 项目结构

```
crypto-briefing/
├── .github/workflows/
│   └── daily_briefing.yml    ← GitHub Actions 定时任务
├── scripts/
│   ├── config.py             ← 配置文件（标的、阈值、API）
│   ├── data_fetcher.py       ← CoinGecko + Yahoo Finance
│   ├── news_fetcher.py       ← CryptoPanic 新闻
│   ├── ai_analyzer.py        ← Gemini AI 分析
│   ├── feishu_sender.py      ← 飞书推送
│   ├── web_generator.py      ← Web 数据生成
│   └── main.py               ← 主流程
├── docs/                      ← GitHub Pages 根目录
│   ├── index.html            ← Dashboard 页面
│   ├── css/style.css
│   ├── js/app.js
│   └── data/                 ← 每日 JSON 数据
│       ├── latest.json
│       ├── index.json
│       └── YYYY-MM-DD.json
└── requirements.txt
```

## 数据源

| 数据 | 来源 | 费用 |
|------|------|------|
| 加密货币价格 | CoinGecko API | 免费 |
| 美股/港股价格 | Yahoo Finance | 免费 |
| 加密新闻 | RSS 订阅源 (CoinDesk, CoinTelegraph等) | 免费 |
| AI 分析 + 搜索 | Gemini API (Google Search) | 免费 |
| 定时运行 | GitHub Actions | 免费 |
| 网页托管 | GitHub Pages | 免费 |
| 消息推送 | 飞书 Webhook | 免费 |

**总费用：¥0 / 月**

## License

MIT
