# 投资组合追踪器 (Portfolio Tracker)

一套自托管的投资组合仪表盘，从盈透证券 (Interactive Brokers, IBKR) 拉取实时持仓，自动补全公司信息和分析师预期，保存历史快照，并通过简洁的深色 UI 展示，附带 TradingView 一键链接。

English version: [README.md](README.md).

## 功能介绍

- 通过本地 socket API 连接 IB Gateway，拉取所有账户里的所有持仓
- 通过 IBKR 的合约详情自动补全公司全名、行业分类、自动分级 (无需 API key)
- 通过 Yahoo Finance (使用 `curl_cffi` 绕过反爬) 自动补全下次财报日期和预期 EPS 增长率
- Yahoo 被封时自动回退到 Nasdaq 公开 API；如果你提供了 Finnhub 免费 API key 也会自动用上
- 每次同步保存一份持仓快照，方便日后审计
- 深色仪表盘展示：股票代码 / 公司名 / 行业，分级标签，市值，相对成本的总收益，今日 1D 变化，未实现盈亏，财报倒计时徽章，EPS 增长率，TradingView 一键跳转
- 后端使用 PostgreSQL 存储 + FastAPI
- 一键启动器：双击即可启动 Postgres、IB Gateway、后端服务、并打开浏览器

## 系统要求

- 一台 macOS 13 或以上版本的 Mac (Linux 略改即可，Windows 未测)
- 一个盈透证券账户，并下载 IB Gateway (免费)，模拟盘或实盘均可
- 大约 1 GB 可用磁盘空间，首次安装大约 5 分钟

## 安装步骤 (逐行说明)

### 第 1 步：安装 Homebrew (如果你还没装)

打开 "终端" (Cmd+Space 然后输入 "Terminal" 回车)。

输入：

```bash
brew --version
```

如果显示 `Homebrew 4.x.x`，跳到第 2 步。

如果显示 `command not found`，运行下面这一行安装 Homebrew：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

会要求你输入 Mac 密码。输入后回车 (输入时不会显示字符，这是正常的)。等大约 5 分钟。结束后复制并运行它显示的两条 `echo` 命令。然后关掉终端再开一个新的。

### 第 2 步：安装 Postgres、Python 和 Node

三个包，一条命令：

```bash
brew install postgresql@16 python@3.11 node
```

每个包大约需要 30 秒到几分钟。

启动 Postgres 服务，让它开机自启：

```bash
brew services start postgresql@16
```

确认 Postgres 正在运行：

```bash
brew services list
```

应该看到 `postgresql@16  started`。如果不对，把输出粘到搜索引擎查一下，通常是权限问题。

把 `psql` 加到 PATH：

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
psql --version
```

应该看到 `psql (PostgreSQL) 16.x`。

### 第 3 步：安装 IB Gateway

去 https://www.interactivebrokers.com/en/index.php?f=14099 点 "Download IB Gateway"，选 **stable** 版本 (不是 latest)，运行安装包。安装好之后，IB Gateway 会装在 `~/Applications/IB Gateway 10.xx/`。

打开 IB Gateway，选 **Live** 或 **Paper**，登录。第一次登录时手机上的 IBKR 会推送 2FA 验证，点接受。建议勾选 "Memorize this device"，下一周内的登录就不用再点 2FA。

Gateway 显示三个绿条 (API Server connected, Market Data Farm ON, Historical Data Farm ON) 之后，进 `Configure → Settings → API → Settings`：

1. 勾选 "Enable ActiveX and Socket Clients"
2. 确认 Socket port 是 4001 (实盘) 或 4002 (模拟盘)
3. 把 127.0.0.1 加到 Trusted IPs (没有的话点 Create，输入 127.0.0.1，OK)
4. **保留 "Read Only API" 勾选** (本工具只读持仓数据，这样可以防止任何意外下单)

点 Apply 然后 OK。

### 第 4 步：克隆这个仓库

终端里：

```bash
cd ~/Documents
git clone https://github.com/<你的用户名>/portfolio-tracker.git
cd portfolio-tracker
```

把 `<你的用户名>` 换成你的 GitHub 用户名。

### 第 5 步：建数据库

```bash
createdb portfolio
psql -d portfolio -f backend/init_db.sql
```

会看到一系列 `CREATE TABLE` 和 `ALTER TABLE`。第一行那个 "database portfolio already exists" 的报错是预期的，可以忽略。

确认表已经建好：

```bash
psql -d portfolio -c "\dt"
```

应该能看到 `metadata`、`positions`、`position_history`、`trades` 这四张表。

### 第 6 步：配置后端

```bash
cp backend/.env.example backend/.env
```

用任意编辑器打开 `backend/.env`：

```bash
open -a TextEdit backend/.env
```

需要改 4 个地方：

1. `IBKR_PORT=4002` 如果你登录的是模拟盘；`IBKR_PORT=4001` 如果是实盘
2. `DATABASE_URL=postgresql+psycopg2://你的Mac用户名@localhost:5432/portfolio` — 把 `你的Mac用户名` 换成在终端运行 `whoami` 显示的内容
3. `IBKR_READONLY=true` — 强烈建议保持 true，除非你明确要用 API 下单
4. (可选) `FINNHUB_API_KEY=` — 先留空，只在 Yahoo 和 Nasdaq 都被封时才需要

保存关闭。

### 第 7 步：安装 Python 依赖

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

最后一条命令大约需要 1 到 3 分钟。会装 FastAPI、ib_insync、SQLAlchemy、yfinance、curl_cffi 等等。

### 第 8 步：安装 Node 依赖并构建前端

打开新的终端标签 (Cmd+T)：

```bash
cd ~/Documents/portfolio-tracker/frontend
npm install
npm run build
```

`npm install` 大约 30 到 60 秒；`npm run build` 再来 20 秒。结果是构建好的静态前端文件 `frontend/dist/`。

### 第 9 步：安装桌面启动器 (可选但推荐)

回到项目根目录：

```bash
cd ~/Documents/portfolio-tracker
chmod +x start.command stop.command scripts/*.sh
bash scripts/install_desktop_launcher.sh
```

桌面会出现两个图标：`Portfolio Tracker.command` 和 `Portfolio Tracker (stop).command`。

### 第 10 步：启动

确保 IB Gateway 已经打开并登录。然后双击桌面上的 `Portfolio Tracker.command`。

终端会闪一下出现，30 秒内你的默认浏览器会自动打开 `http://127.0.0.1:8000` 显示仪表盘。可以关掉那个终端窗口，后端会在后台继续运行。

之后想停掉所有服务，双击 `Portfolio Tracker (stop).command`。

## 日常使用

1. 打开 IB Gateway (如果你勾了 "Save settings"，密码会自动填好；如果手机上勾了 "Memorize this device"，连 2FA 也不用)
2. 双击 `Portfolio Tracker.command`
3. 浏览器打开仪表盘

就这么简单。后端默认每 15 分钟自动同步一次。点仪表盘右下角的 `force sync` 可以立即刷新。

## 仪表盘各列说明

- **Ticker / Company**: 上方股票代码，下方公司全名，再下方行业
- **Tier 标签**: 自动分到 T1 半导体&AI核心、T2 能源&材料、T3 工业、T4 医药、T5 其他。点铅笔图标可以手动覆盖
- **Mkt Value**: 持仓市值
- **Avg Cost**: 加权平均成本价 (含手续费)
- **Current**: IBKR 提供的最新价格
- **Gain**: 持仓总收益百分比，绿正红负
- **1D**: 今日相对昨收的涨跌幅，绿正红负，鼠标悬停显示美元数额
- **Unrealized**: 未实现盈亏 (美元)
- **Next ER**: 下次财报日期，配倒计时徽章 (红 ≤3 天，橙 ≤7 天，黄 ≤14 天)
- **EPS Growth**: 分析师预期的下一年 EPS 相对过去 12 个月的增长率 (百分比)
- **图表图标**: 在新标签页打开 TradingView
- **铅笔图标**: 弹出编辑窗口，可改 tier、行业、EPS 文字、财报日期、交易所覆盖、备注

底部条显示组合平均收益、领涨股、盈利股票数、以及 14 天内有财报的票。

页面右上角有 PT / EST / BJT 时区选择器，你的选择会跨刷新保留。

## 系统架构

```
IB Gateway (端口 4001/4002)
        │
        ▼
ib_insync ──▶ FastAPI 后端 ──▶ Postgres
        │                    │
        ▼                    ▼
   Yahoo (curl_cffi),    React + Vite 前端
   Nasdaq, Finnhub        (一次构建，由 FastAPI 提供静态文件)
```

- `backend/app/main.py`: FastAPI 入口，生命周期、定时器、CORS、挂载已构建的前端
- `backend/app/ibkr/client.py`: ib_insync 封装，拉取持仓和合约详情
- `backend/app/services/sync.py`: 单次同步流程编排：IBKR → Yahoo 昨收 → Postgres
- `backend/app/services/enrichment.py`: 公司名、行业、tier、EPS 增长率、下次财报
- `backend/app/scheduler.py`: APScheduler，每 N 分钟跑一次同步
- `backend/app/routers/`: HTTP 接口 — `positions`、`portfolio`、`history`、`metadata`、`sync`、`health`
- `frontend/src/`: React 组件、hooks、工具函数

## 常见问题

**IB Gateway 显示红条，仪表盘是空的。**
你需要登录 Gateway。打开 Gateway 登录，等三个绿条出现，然后在仪表盘点 `force sync`。

**`curl: (7) Failed to connect to localhost port 8000`**
后端没在跑。重新双击 `Portfolio Tracker.command`，或者手动启动：`cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000`。

**仪表盘对 sync 请求返回 "Method Not Allowed"。**
后端代码版本旧了。重新构建并重启：先停掉所有服务，运行 `cd frontend && rm -rf dist && npm run build`，再重新跑 `Portfolio Tracker.command`。

**日志里有大量 Yahoo 429 Too Many Requests。**
你的 IP 被 Yahoo 限流了，连 curl_cffi 都救不回来。去 https://finnhub.io 注册一个免费 key，把 `FINNHUB_API_KEY=xxx` 加到 `backend/.env`，然后重启。系统会改用 Finnhub 拉财报和 EPS 数据。

**价格看起来不对/有延迟。**
你的 IBKR 账户没订阅美股实时行情，Gateway 给到的是 15 到 20 分钟延迟数据。可以接受延迟、去 IBKR 账户管理订阅 (基础包大约每月 $4.50)、或者承认盘中精度有限。

**`pkill -f ibgateway` 没用，Gateway 卡死了。**
在 Dock 上右键 Gateway 图标选 Quit。如果还不行，Cmd+Option+Esc 强制退出。

**仪表盘不会自动在浏览器打开。**
手动访问 `http://127.0.0.1:8000`。如果能打开，是自动启动浏览器那一步偶尔失败 (无伤大雅)。如果打不开，看项目根目录的 `.logs/backend.log`。

## 许可证

MIT 协议。详见 `LICENSE` 文件。

## 致谢

- ib_insync — Ewald de Wit
- yfinance / yahooquery 社区
- curl_cffi 的 TLS 指纹模拟
- IBC Alpha 的 Gateway 自动化方案
