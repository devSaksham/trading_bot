# Binance Futures Testnet Trading Bot

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance API wrapper (auth, signing, HTTP)
│   ├── orders.py          # Order placement logic (MARKET, LIMIT, STOP_MARKET)
│   ├── validators.py      # Input validation
│   └── logging_config.py  # File + console logging setup
├── cli.py                 # Entry point (argparse CLI)
├── logs/
│   ├── market_order.log   # Sample market order log
│   └── limit_order.log    # Sample limit order log
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone / unzip the project

```bash
cd trading_bot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your Testnet API credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Go to **API Key** tab → Generate a key pair
4. Copy the **API Key** and **Secret Key**

### 5. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```
API_KEY=your_testnet_api_key_here
API_SECRET=your_testnet_api_secret_here
```

---

## How to Run

### Check connection / price

```bash
# Check current BTC price
python cli.py --price-check BTCUSDT

# Check account balance
python cli.py --balance
```

### Place a Market Order

```bash
# Market BUY 0.01 BTC
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Market SELL 0.5 ETH
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.5
```

### Place a Limit Order

```bash
# Limit BUY 0.01 BTC at $40,000
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 40000

# Limit SELL 0.5 ETH at $3,000
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.5 --price 3000
```

### Place a Stop-Market Order (Bonus)

```bash
# Stop-loss: SELL 0.01 BTC if price drops to $60,000
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 60000
```

### Interactive Mode (guided prompts)

```bash
python cli.py --interactive
```

---

---

## Logging

All API requests, responses, and errors are written to `logs/trading_bot.log`.

- **Console** → INFO level and above (clean, human-readable)
- **Log file** → DEBUG level and above (full detail including raw API params and responses)

Log format:
```
2024-01-15 10:23:42 | INFO     | orders:72 | Placing MARKET BUY order | symbol=BTCUSDT | qty=0.01
```

---

## Assumptions

- All trading is done on **Binance Futures Testnet (USDT-M)** — not real money
- Base URL: `https://testnet.binancefuture.com`
- Default `timeInForce` for LIMIT orders is **GTC** (Good Till Cancelled)
- Quantity precision must match the symbol's lot size rules on Binance (e.g. BTCUSDT min qty is 0.001)
- API credentials are stored in a `.env` file and never hardcoded

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing required CLI args | Prints usage hint, exits cleanly |
| Invalid input (bad symbol, qty=0) | Validation error printed, no API call made |
| Binance API error (e.g. -2010 insufficient balance) | Error code + message printed and logged |
| Network timeout | Retried 3 times with backoff, then error shown |
| Missing API keys in .env | Immediate exit with clear message |

---

## Requirements

- Python 3.8+
- `requests` — HTTP client
- `python-dotenv` — loads `.env` file
- `urllib3` — retry logic (used by requests)
