# Portfolio Tracker

A self hosted dashboard that pulls your live positions from Interactive Brokers, enriches them with company data and analyst estimates, stores historical snapshots, and renders everything in a clean dark mode UI with one click TradingView links.

中文说明请看 [README.zh.md](README.zh.md).

## What it does

- Connects to IB Gateway over its local socket API and pulls every position across every account
- Fills in company name, industry, and tier classification using IBKR contract details (no API key required)
- Fills in next earnings date and forward EPS growth using Yahoo Finance via `curl_cffi` to bypass rate limits
- Falls back to Nasdaq's public API if Yahoo blocks you, and to Finnhub if you provide a free API key
- Stores a position snapshot every sync so you can audit P&L over time
- Renders a dark mode dashboard with: ticker / company name / sector, tier badge, market value, gain since cost basis, today's 1D change, unrealized P&L, next earnings countdown, EPS growth, and a click through to TradingView
- Uses Postgres for storage and FastAPI for the backend
- One double click launcher that brings up Postgres, IB Gateway (you log in once), the backend, and your browser

## Requirements

You need a Mac with macOS 13 or later. Linux works with minor tweaks; Windows is untested.

You need an Interactive Brokers account with a downloaded IB Gateway (free). Live or paper, either works.

You need around 1 GB of free disk space and 5 minutes for first time setup.

## Setup, line by line

### Step 1: install Homebrew (if you don't already have it)

Open the Terminal app (press Cmd+Space, type Terminal, press Enter).

Type:

```bash
brew --version
```

If it prints a version like `Homebrew 4.x.x`, skip to Step 2.

If it says "command not found", install Homebrew with this single line:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

It will ask for your Mac password. Type it and press Enter (no characters will show, that's normal). Wait for it to finish (about 5 minutes). At the end, copy and run the two `echo` commands it prints. Close the Terminal and reopen it.

### Step 2: install Postgres, Python, and Node

Three packages, one command:

```bash
brew install postgresql@16 python@3.11 node
```

Each `brew install` takes 30 seconds to a few minutes.

Start the Postgres service so it runs automatically:

```bash
brew services start postgresql@16
```

Verify Postgres is running:

```bash
brew services list
```

You should see `postgresql@16  started`. If not, paste the output to a search engine; usually a permission issue.

Make sure `psql` is on your PATH:

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
psql --version
```

You should see `psql (PostgreSQL) 16.x`.

### Step 3: install IB Gateway

Go to https://www.interactivebrokers.com/en/index.php?f=14099 and click "Download IB Gateway". Choose the **stable** edition (not the latest). Run the installer. After it finishes, IB Gateway lives at `~/Applications/IB Gateway 10.xx/`.

Open IB Gateway, choose **Live** or **Paper**, and log in. The first login asks you to approve a 2FA prompt on your phone via the IBKR mobile app. Tap accept. Tick "Memorize this device" so future logins skip the prompt for a week.

Once Gateway shows three green bars (API Server connected, Market Data Farm ON, Historical Data Farm ON), open `Configure → Settings → API → Settings`:

1. Tick "Enable ActiveX and Socket Clients"
2. Confirm Socket port reads 4001 (live) or 4002 (paper)
3. Make sure 127.0.0.1 is in Trusted IPs (if not, click Create, type 127.0.0.1, OK)
4. Leave "Read Only API" ticked (the tracker only reads positions; this prevents any accidental order)

Click Apply, then OK.

### Step 4: clone this repository

In the Terminal:

```bash
cd ~/Documents
git clone https://github.com/<your-username>/portfolio-tracker.git
cd portfolio-tracker
```

Replace `<your-username>` with your actual GitHub username.

### Step 5: create the database

```bash
createdb portfolio
psql -d portfolio -f backend/init_db.sql
```

You should see a series of `CREATE TABLE` and `ALTER TABLE` lines. The first error about "database portfolio already exists" is harmless and expected.

Verify the tables exist:

```bash
psql -d portfolio -c "\dt"
```

You should see `metadata`, `positions`, `position_history`, and `trades`.

### Step 6: configure the backend

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` in any text editor:

```bash
open -a TextEdit backend/.env
```

Edit four lines:

1. `IBKR_PORT=4002` if you logged into a paper account, or `IBKR_PORT=4001` if live
2. `DATABASE_URL=postgresql+psycopg2://YOUR_MAC_USERNAME@localhost:5432/portfolio` — replace `YOUR_MAC_USERNAME` with the output of running `whoami` in Terminal
3. `IBKR_READONLY=true` — keep this true unless you have a specific reason to allow trading via the API
4. (Optional) `FINNHUB_API_KEY=` — leave blank for now; only needed if Yahoo and Nasdaq both block you

Save and close.

### Step 7: install Python dependencies

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

The last command takes 1 to 3 minutes. It installs FastAPI, ib_insync, SQLAlchemy, yfinance, curl_cffi, and friends.

### Step 8: install Node dependencies and build the frontend

In a new Terminal tab (Cmd+T):

```bash
cd ~/Documents/portfolio-tracker/frontend
npm install
npm run build
```

`npm install` takes 30 to 60 seconds. `npm run build` takes another 20 seconds. The output is a static dashboard at `frontend/dist/`.

### Step 9: install the desktop launcher (optional but recommended)

Back in the project folder:

```bash
cd ~/Documents/portfolio-tracker
chmod +x start.command stop.command scripts/*.sh
bash scripts/install_desktop_launcher.sh
```

You'll get two icons on your Desktop: `Portfolio Tracker.command` and `Portfolio Tracker (stop).command`.

### Step 10: launch

Make sure IB Gateway is open and logged in. Then double click `Portfolio Tracker.command` on your Desktop.

A Terminal window flashes open. Within 30 seconds your default browser opens to `http://127.0.0.1:8000` and the dashboard appears. Close the Terminal window when done; the backend keeps running in the background.

Stop everything later with `Portfolio Tracker (stop).command`.

## Daily use

1. Open IB Gateway (your password is saved if you ticked "Save settings"; if you also ticked "Memorize this device" on your phone, even the 2FA is skipped)
2. Double click `Portfolio Tracker.command`
3. Dashboard opens in your browser

That's it. The backend auto syncs every 15 minutes by default. Click `force sync` in the dashboard's bottom right to refresh on demand.

## Features in the dashboard

- **Ticker / Company column**: ticker on top, full company name underneath, sector below that
- **Tier badge**: auto classified into T1 Semi & AI Core, T2 Energy & Materials, T3 Industrials, T4 Healthcare, T5 Other. Click the pencil icon to override
- **Mkt Value**: position size in dollars
- **Avg Cost**: your weighted average entry price including commissions
- **Current**: latest market price from IBKR
- **Gain**: total return since you opened the position, colored pill
- **1D**: today's change versus yesterday's close, colored pill, hover for dollar amount
- **Unrealized**: unrealized profit or loss in dollars
- **Next ER**: next earnings date with a colored urgency badge (red ≤3 days, orange ≤7 days, yellow ≤14 days)
- **EPS Growth**: forward EPS analyst consensus vs trailing twelve months, expressed as a percentage
- **Chart icon**: opens TradingView for that ticker in a new tab
- **Pencil icon**: opens a modal to edit tier, sector, EPS guidance text, next earnings date, exchange override, and notes

The bottom strip shows portfolio averages, top performer, win count, and any tickers with earnings within 14 days.

The header has a PT / EST / BJT timezone picker. Your choice persists between reloads.

## Architecture

```
IB Gateway (port 4001/4002)
        │
        ▼
ib_insync ──▶ FastAPI backend ──▶ Postgres
        │                       │
        ▼                       ▼
   Yahoo (curl_cffi),      React + Vite frontend
   Nasdaq, Finnhub          (built once, served from FastAPI)
```

- `backend/app/main.py`: FastAPI entrypoint, lifespan, scheduler, CORS, mounts the built frontend
- `backend/app/ibkr/client.py`: ib_insync wrapper, fetches positions and contract details
- `backend/app/services/sync.py`: orchestrates one sync cycle: IBKR → Yahoo previous close → Postgres
- `backend/app/services/enrichment.py`: company name, industry, tier, EPS growth, next earnings
- `backend/app/scheduler.py`: APScheduler running sync every N minutes
- `backend/app/routers/`: HTTP endpoints — `positions`, `portfolio`, `history`, `metadata`, `sync`, `health`
- `frontend/src/`: React components, hooks, utilities

## Troubleshooting

**IB Gateway shows red bars and the dashboard is empty.**
You need to log into Gateway. Open Gateway, log in, wait for the three green bars, then click `force sync` in the dashboard.

**`curl: (7) Failed to connect to localhost port 8000`**
The backend is not running. Run `Portfolio Tracker.command` again, or start manually: `cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000`.

**Dashboard says "Method Not Allowed" on a sync request.**
The backend code is out of date. Rebuild and restart: stop everything, run `cd frontend && rm -rf dist && npm run build`, then `Portfolio Tracker.command` again.

**Yahoo returns 429 Too Many Requests in the logs.**
Yahoo is rate limiting your IP even with curl_cffi. Sign up at https://finnhub.io for a free API key, add `FINNHUB_API_KEY=xxx` to `backend/.env`, and restart. The tracker will use Finnhub for earnings and EPS instead.

**Prices look stale.**
You don't have a US market data subscription on your IBKR account, so Gateway feeds delayed (15 to 20 minute) data. Either accept the delay, subscribe in IBKR Account Management (about $4.50/month for the basic), or accept that intraday accuracy is limited.

**`pkill -f ibgateway` doesn't help; Gateway is unresponsive.**
Quit Gateway from its Dock icon (right click, Quit). If it refuses, force quit via Cmd+Option+Esc.

**The dashboard never opens in my browser.**
Visit `http://127.0.0.1:8000` manually. If that works, the auto open hook misfired (harmless). If it doesn't load, check the backend log at `.logs/backend.log` from the project root.

## License

MIT. See `LICENSE`.

## Acknowledgements

- ib_insync by Ewald de Wit
- yfinance and yahooquery communities
- curl_cffi for the TLS impersonation magic
- IBC Alpha for the Gateway automation patterns
