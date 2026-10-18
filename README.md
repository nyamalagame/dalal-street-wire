# Dalal Street Wire

A single-page dashboard that pulls Indian financial news from public RSS feeds into one filterable stream.

## Features

- 44 news feeds from 17 outlets: Economic Times, Mint, Business Standard, Moneycontrol, BusinessLine, Financial Express, CNBC-TV18, Business Today, Zee Business, ThePrint, Mostly Economics, Trading Economics, The Hindu, ETBFSI, Trade Brains, EquityPandit and Alpha Ideas, plus BSE's Sensex view
- 13 official exchange feeds from NSE and BSE (announcements, financial results, board meetings, corporate actions, insider trading, offer documents, circulars and notices), shown in their own **Exchange filings** tab so they don't crowd the news
- One merged stream, de-duplicated and grouped by day in IST
- Compact headline list by default (time, source and headline only); a toggle shows summaries, tags and images
- Main tabs: All, Stock picks, Markets, Earnings; IPOs, Banking & RBI, Economy, Commodities and Exchange filings are under **More**
- Search behind the magnifier button, and a **Show more** button for older stories
- Outlets, feed health and fetch details in a **Sources** panel opened from the header
- **Stock picks** tab that highlights brokerage and analyst calls, with the rating, target price and brokerage read from each headline
- News fetched automatically every 30 minutes, plus a manual fetch any time
- NSE market open/closed indicator

## Running it

Open `index.html` in any modern browser. There is nothing to install or build.

## How it fetches the news

A GitHub Actions job (`.github/workflows/fetch-feeds.yml`) runs `scripts/fetch_feeds.py` every 30 minutes, all day, every day (48 runs a day). The script reads the feed list from `index.html`, fetches every feed on GitHub's servers and writes a compact snapshot, `data/feeds.json`. The job then publishes the dashboard and that snapshot straight to GitHub Pages. Nothing is committed, so the repository holds only the code.

The dashboard loads the snapshot from its own address, so it works in any browser, including Brave with Shields on, and loads quickly on phones. The snapshot keeps each story's headline, link, date, image link and a one-sentence teaser; the full story is always on the publisher's site.

**Setup:** in the repository's **Settings → Pages**, set **Source** to **GitHub Actions**.

**To get fresh news right away:** open the **Actions** tab, choose **Fetch feeds and publish** and click **Run workflow** (the dashboard's **Open fetch page** button goes straight there). The site updates about two minutes later. Pushing a change to `main` also republishes the site with fresh news.

To change the schedule, edit the `cron` lines in the workflow. Cron times are in UTC, and IST is UTC+5:30.

GitHub pauses scheduled jobs in public repositories after 60 days without repository activity and emails a warning first. If that happens, re-enable the job from the **Actions** tab.

To add or remove a feed, edit the `FEEDS` list in `index.html`.

When `index.html` is opened directly from your device (not through GitHub Pages), there is no snapshot to read, so the page falls back to fetching each feed through a free CORS proxy: allorigins.win, corsproxy.io, codetabs.com or rss2json.com, in that order. Some browsers, Brave included, block these proxies.

If a feed shows red in the health panel, hover over it to see the error.

## Limitations

- Some feed URLs come from public feed directories and haven't been individually verified. Moneycontrol in particular may no longer publish public RSS feeds.
- The market indicator follows NSE equity hours (09:15–15:30 IST, Monday to Friday) and doesn't know about exchange holidays.
- Stock picks are detected by matching patterns in headlines, so ratings, targets or brokerage names can be missed or misread.

## Disclaimer

This dashboard only collects headlines published by news outlets. Nothing in it is investment advice. Always read the full article and do your own research before acting on any call.

All headlines, summaries and links belong to their respective publishers.
