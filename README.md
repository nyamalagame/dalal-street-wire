# Dalal Street Wire

A single-page dashboard that pulls Indian financial news from public RSS feeds into one filterable stream.

## Features

- 40 news feeds from 14 outlets: Economic Times, Mint, Business Standard, Moneycontrol, BusinessLine, Financial Express, CNBC-TV18, Business Today, Zee Business, ThePrint, Mostly Economics, Trading Economics, The Hindu and ETBFSI
- 7 official NSE feeds (announcements, financial results, board meetings, corporate actions, insider trading, offer documents and circulars), shown in their own **NSE filings** tab so they don't crowd the news
- One merged stream, de-duplicated and grouped by day in IST
- Category tabs: Stock picks, NSE filings, Markets, Earnings, IPOs, Banking & RBI, Economy, Commodities
- **Stock picks** tab that highlights brokerage and analyst calls, with the rating, target price and brokerage read from each headline
- Keyword search and per-outlet toggles
- Feed health panel showing which feeds loaded and which failed
- Auto-refresh every 10 minutes and an NSE market open/closed indicator

## Running it

Open `index.html` in any modern browser. There is nothing to install or build.

## How it fetches the news

Browsers block a page from reading other websites directly (CORS), so the dashboard fetches each RSS feed through a free CORS proxy. It tries these in order and remembers the one that works:

1. allorigins.win
2. corsproxy.io
3. codetabs.com
4. rss2json.com

Free proxies can rate-limit or go down. To reduce that, feeds load six at a time. If a feed shows red in the health panel, hover over it to see the error.

## Limitations

- Some feed URLs come from public feed directories and haven't been individually verified. Moneycontrol in particular may no longer publish public RSS feeds.
- The market indicator follows NSE equity hours (09:15–15:30 IST, Monday to Friday) and doesn't know about exchange holidays.
- Stock picks are detected by matching patterns in headlines, so ratings, targets or brokerage names can be missed or misread.

## Disclaimer

This dashboard only collects headlines published by news outlets. Nothing in it is investment advice. Always read the full article and do your own research before acting on any call.

All headlines, summaries and links belong to their respective publishers.
