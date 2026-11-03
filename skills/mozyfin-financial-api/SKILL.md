---
name: mozyfin-financial-api
description: Complete developer guide, endpoint catalog, and mandatory normalization rules for the Mozyfin (Antofin) AI Financial & Market Data API. Use when querying Vietnam market entities, OHLCV charts, market indices, watchlists, top stocks, financial statements, corporate events, or AI financial agent chat.
---

# Mozyfin Financial & Market Data API Guide

The Mozyfin API (`https://partner-api.mozyfin.com` & `https://invest.index.vn`) provides production-grade market data, company financials, historical quotes, corporate events, and AI financial agents for the Vietnamese equity and financial markets.

## 1. Authentication & Configuration

Every request to `https://partner-api.mozyfin.com` must include the API key in the `X-API-Key` HTTP header:
```bash
curl -H "X-API-Key: $MOZY_API_KEY" "https://partner-api.mozyfin.com/api/v1/market/exchange/entity?limit=10"
```

Environment variables:
```env
MOZY_API_KEY=mozy_ak_live_...
MOZY_API_BASE_URL=https://partner-api.mozyfin.com
```

---

## 2. Mandatory Pitfalls & Normalization Rules (CRITICAL — NEVER MISS)

### Rule 1: Market Index Tickers MUST Always Include `.VN` Suffix
- **Endpoint**: `GET /api/v2/market/market-index/{ticker}/ohlcv?timeframe=1d&limit=12`
- **Mandatory Ticker Mapping**:
  - `VN-INDEX` / `VNINDEX` -> **`VNINDEX.VN`**
  - `VN30` / `VN30-INDEX` -> **`VN30.VN`**
  - `HNX-INDEX` / `HNX` -> **`HNX.VN`**
  - `UPCOM-INDEX` / `UPCOM` -> **`UPCOM.VN`**
  - `VN100` / `VN100-INDEX` -> **`VN100.VN`**
  - `HNX30` / `HNX30-INDEX` -> **`HNX30.VN`**
- **Why**: Calling `/api/v2/market/market-index/VNINDEX/ohlcv` **without `.VN`** does NOT return 404 — it returns `200 OK` with empty arrays `{"t":[],"o":[],"h":[],"l":[],"c":[],"v":[]}`! That silent empty array causes routes (like `watchlist-monitor`) to fall back to hardcoded numbers and overwrite live SSR index quotes on client `useEffect` hydration.
- **Single-Source Formula Across All Index Widgets (Watchlist, Running Bar, Market Indices Cards & Chart)**:
  ```ts
  const closes = d.c.map(v => Number(v) || 0).filter(v => v > 0);
  const points = closes[closes.length - 1] ?? 0;
  const prevClose = closes.length >= 2 ? (closes[closes.length - 2] ?? points) : (Number(d.o?.[d.o.length - 1]) || points);
  const change = Number((points - prevClose).toFixed(2));
  const changePercent = prevClose > 0 ? Number((((points - prevClose) / prevClose) * 100).toFixed(2)) : 0;
  ```

### Rule 2: Entity `change_percent` & Matched `volume` Normalization
- **`change_percent` Decimal Ratio**: In `GET /api/v1/market/exchange/entity`, `change_percent` is returned as a **decimal ratio** (`0.0901` = `+9.01%`), or `0` on some exchanges even when `change_value !== 0`.
  - Always compute/verify percentage change from `change_value` and `current_price`:
    ```ts
    const prevClose = current_price - change_value;
    const pctFromChange = prevClose > 0 ? (change_value / prevClose) * 100 : 0;
    ```
  - If using `change_percent` directly and `Math.abs(rawPct) > 0 && Math.abs(rawPct) < 1`, multiply by `100`.
- **Matched Volume (`volume`)**: `/api/v1/market/exchange/entity` only provides `avg_volume_10d` / `avg_volume_3m`, NOT the current session's matched volume (`total_volume`).
  - Always enrich current session volume (`v[v.length - 1]`) and 7-session sparkline closes (`c`) via batch OHLCV:
    `GET /api/v2/market/exchange/entity/ohlcv/batch?symbols=HPG.VN,VCB.VN&timeframe=1d&limit=7` (note the `.VN` suffix on every stock symbol).

### Rule 3: Sector Name & Real vs. Unsupported Endpoints
- **Sector Name**: Read directly from `entity.sector?.local_name || entity.sector?.name` on `/api/v1/market/exchange/entity`.
- **Market-Wide Foreign Flow (20 Sessions)**: Fetch from `GET https://invest.index.vn/api/market-monitor/foreign-flow` (`latest.net_value` & `series`).
- **AI Watchlist Sentiment & Spotlight**: Fetch from `GET https://invest.index.vn/api/market-monitor/watchlist` and `GET https://invest.index.vn/api/market-monitor/overview`.
- **Unsupported Endpoints (Do Not Fabricate)**:
  - Per-stock daily foreign buy/sell (`GET /api/v1/market/entity/{id}/quote/history` returns `404`).
  - Per-stock hourly social mention counts (`mentions24h` / `hourlyMentions`).
  - Hide UI tabs/columns that depend on unsupported per-stock foreign flow or social mention counts unless a real backend endpoint is provided.

---

## 3. API Endpoint Catalog

### A. Market & Entities (Bảng giá & Danh sách cổ phiếu)
- **`GET /api/v1/market/exchange/entity`** (List entities)
  - **Query parameters**:
    - `page` (int, default 1), `limit` (int, default 20, max 100)
    - `search` (string): Search by name, symbol, or description (`HPG`, `VCB`)
    - `exchange_ids` (string[]): `["HOSE", "HNX", "UPCOM"]`
    - `sort_by` (`name`, `symbol`, `current_price`, `market_cap`), `sort_order` (`asc`, `desc`)
  - **Response fields per entity**:
    - `symbol`, `name`, `short_name`, `local_name`, `local_short_name`
    - `current_price`, `change_value`, `change_percent` (decimal ratio!)
    - `market_cap`, `shares_outstanding`, `free_shares`, `foreign_ownership`
    - `pe`, `eps`, `beta`, `dividend`, `dividend_yield`
    - `avg_volume_10d`, `avg_volume_3m`, `high_52_week`, `low_52_week`, `price_change_1y`
    - `exchange_id` (`HOSE`, `HNX`, `UPCOM`), `sector` (`{ id, name, local_name }`), `logo_url`

### B. Historical Charts & High-Performance OHLCV (Columnar)
- **`GET /api/v2/market/market-index/{ticker}.VN/ohlcv?timeframe=1d&limit=12`**: Historical OHLCV for market indices (`VNINDEX.VN`, `VN30.VN`, `HNX.VN`, `UPCOM.VN`) formatted as `{ t, o, h, l, c, v }`.
- **`GET /api/v2/market/exchange/entity/{symbol}.VN/ohlcv?timeframe=1d&limit=30`**: OHLCV for a single stock ticker (`.VN` required).
- **`GET /api/v2/market/exchange/entity/ohlcv/batch?symbols=HPG.VN,VCB.VN&timeframe=1d&limit=7`**: Batch OHLCV for multiple stock tickers in a single HTTP request (`.VN` required on each symbol).

### C. Fundamentals, Corporate Actions & Ownership
- **`GET /api/v1/market/entity/{id}/event`**: Corporate actions, cash/stock dividends, ex-rights dates, AGM meetings.
- **`GET /api/v1/market/entity/{id}/financial-statement`**: Balance sheet, Income statement, Cash flows.
- **`GET /api/v1/market/entity/{id}/financial-statistic`**: Key financial metrics (ROA, ROE, Net Margin, Debt/Equity).
- **`GET /api/v1/market/entity/{id}/holder`**: Major institutional and individual shareholders.
- **`GET /api/v1/market/entity/{id}/officer`**: Board of directors and management team.

### D. AI Financial Agent Chat & Market Monitor (`invest.index.vn`)
- **`POST /api/v1/chat`** & **`POST /api/v1/chat/{chat_id}/message`**: AI financial chat session & streaming responses.
- **`GET https://invest.index.vn/api/market-monitor/foreign-flow`**: 20-session market-wide foreign buy/sell/net flow.
- **`GET https://invest.index.vn/api/market-monitor/watchlist`**: AI sentiment scores (`score`, `label`) for key stocks.
