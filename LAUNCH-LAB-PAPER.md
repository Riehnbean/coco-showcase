# Launch Lab: an honest, plain-English XRP research dashboard

**Zach Riehn** · October 2026 · Live at **[cocoeatsai.com/area4](https://cocoeatsai.com/area4/)** · [How it works](https://cocoeatsai.com/area4/methodology/)

> **Living document.** This describes the current model as of October 2026. Launch Lab is actively being improved, so the models, features and numbers here will change over time. The live site and its public track record are always the most current version.
>
> This paper describes the design, methods and measured results of Launch Lab. The product code and model settings are proprietary and are not in this repository. Research and education only, not financial advice.

---

## Abstract

Launch Lab is a free web dashboard for XRP. It is built for people who are not traders: "anyone and their grandma" should be able to open it and understand what is going on in one minute.

It combines:
- a live chart;
- 24-hour and 7-day outlooks, each with a probability and a price range;
- a public, never-edited track record;
- a "money flows" view (exchange wallets, whale payments, Ripple's dollar coin RLUSD, Ripple escrow, ETF flows);
- a crash-preparedness kit;
- a dated calendar of XRP Ledger upgrades and industry events.

The guiding rule is **honesty over hype**:
- Every number comes with how often it has been right.
- Weak signals are labeled weak.
- The record restarts in public when the model changes.

In testing, the 24-hour direction call was right about 61% of the time when the model picked a side, and the price ranges landed inside about as often as they claimed (50% ranges: 49%, 80% ranges: 80%). This paper explains how that was measured, what did *not* work, and where the limits are.

---

## 1. The problem

Most crypto dashboards fail beginners in one of two ways:

1. **Too much noise:** dozens of indicators with no explanation of what they mean or whether they work.
2. **Too much confidence:** "100% accurate signals", cherry-picked wins, no losing record.

Launch Lab tries to be the opposite. It shows a small number of things, explains each in plain English, and says how often each one has actually been right, including when the answer is "about a coin flip."

## 2. Design principles

| Principle | What it means in the product |
|---|---|
| Plain English first | Every number has a one-line explanation and a "how sure is this" label. Jargon is defined on hover. |
| Show the odds, not just the call | Each outlook shows a probability dial and a price range, not just "up" or "down". |
| Always a best guess, honestly labeled | On coin-flip days it still gives a guess, marked "coin-flip zone" with its percentage. |
| Never edit the past | Every call is logged before the outcome is known and checked automatically. Nothing is backfilled. |
| Grade the model people see | When the model changes, the public record restarts. Old calls are archived, not mixed in. |
| Low noise | One screen: chart, two outlook cards, a handful of gauges. Detail lives in drawers. |
| Phone-first | The chart comes first on phones, and every control is at least 40px tall. |

## 3. System overview

```
 Public data sources                    Server (hourly / per-minute jobs)                    Browser
 ─────────────────────                  ───────────────────────────────────────────           ─────────────────
 Binance market data   ───────────────► candles, volatility bands, official call log ──┐
 OKX / Binance futures ───────────────► funding, open interest, liquidations          ├──► Launch Lab page
 XRP Ledger servers    ───────────────► escrow, exchange-wallet balances, whales      │    (chart, outlooks,
 XRPScan               ───────────────► amendment votes, wallet labels                │     gauges, drawers)
 DefiLlama             ───────────────► RLUSD supply                                  │
 Google News / RSS     ───────────────► headlines, tone, ETF flow reports             ┘
                                                                     Binance public stream ──► live price
```

- **Stack:** a static front end with no frameworks. It uses Lightweight Charts and a strict content-security policy (no inline scripts, no third-party trackers).
- **Server:** small Python services with no API keys for public data.
- **Visitors:** no cookies, no accounts, no ads.

## 4. Forecasting method

### 4.1 Two outlooks

| Outlook | Built from | Horizon | What it gives |
|---|---|---|---|
| 24-hour | Hourly candles | Next 24 hours | Direction probability, best guess, 50% and 80% price ranges, chance of a 3%+ move |
| 7-day | Daily candles | Next 7 days | The same, clearly marked low confidence |

Each outlook is a **small, regularized statistical model** built on a handful of market situations that have mattered for XRP historically. Examples:
- a sharp 24-hour drop;
- an unusually low hourly RSI;
- a steady hourly uptrend that tends to stall;
- quiet trading volume;
- a 90-day breakout.

Each situation's historical effect is shown to users next to the base rate. For example: *"Since 2021, higher 24 hours later 62% of the time. Any random hour: 49%."*

Price ranges come from **volatility bands**. Historical outcome quantiles are scaled to current volatility, so the ranges widen in jumpy markets and tighten in calm ones. A separate line gives the empirical 1-in-20 bad case.

### 4.2 Best guess on coin-flip days

When no tested situation is active, the probability sits near 50%. Rather than show "no signal", Launch Lab gives a backup guess. It follows the slight lean when there is one. Otherwise it guesses a reversal of the last 24 hours, which historically was right about 53% of the time on those days. It is displayed as, for example, *"Best guess: higher · 53% · coin-flip zone"*.

### 4.3 How it was tested

- **Strict time order:** the model was fit on older data and tested on later data it had never seen. There was a held-out year, October 2025 to October 2026.
- **Walk-forward:** models were refit month by month and scored only on the following month.
- **One official call per day,** made at the daily close (7 PM Central in summer), so results don't double-count overlapping hours.
- **Base rates and baselines** for every claim: always-up, always-down, momentum and reversal.

## 5. Results

### 5.1 Held-out year (Oct 2025 – Oct 2026)

| Measure | 24-hour | 7-day |
|---|---|---|
| Direction right, when the model picked a side | **61.1%** | 51.1% (≈ coin flip) |
| 50% range contained the outcome | 49.3% (target 50%) | 54.7% |
| 80% range contained the outcome | 80.3% (target 80%) | 83.9% |

The ranges are well calibrated. Daily direction has a modest edge. Weekly direction does not, so it is shown faded and labeled low confidence.

### 5.2 Every-day best guess (one call per day, March 2021 – October 2026, 2,046 days)

| Period | Right | Longest correct streak |
|---|---|---|
| Mar 2021 – Dec 2022 | 56.9% | 8 |
| Jan 2023 – Sep 2025 | 55.1% | 12 |
| Oct 2025 – Oct 2026 | 49.9% | 9 |
| **All days** | **54.7%** | **12** |

Five correct calls in a row happened 45 times, about once every six to seven weeks. **Streaks happen by luck too.** A model that is right 58% of the time hits ten in a row less than 1 time in 100. Launch Lab therefore asks users to judge it over 30+ official calls, not a hot streak.

### 5.3 What did not work (and why it matters)

- **Bigger models made it worse.** Logistic-regression and gradient-boosting models with about 25 inputs (XRP and Bitcoin returns, RSI, trend distance, volatility, volume, day of week) were tested walk-forward. They scored 52–53%, below the small model, because they fit noise. The small model was kept.
- **Patterns fade.** Several historical edges weakened in the last 12 months. For example, panic-hour bounces fell from 61% to 48%. The product shows that next to each pattern instead of hiding it.
- **Trading-strategy tests** in the companion Trading Lab: a momentum strategy (TSI with an EMA filter) beat buy-and-hold on paper (Sharpe 0.94 vs 0.53) and passed walk-forward. It still became a loser once its five best trades were removed, so it was kept as **paper-trade only**. Failed ideas are listed publicly in a "strategy graveyard".

## 6. Track record integrity

- Every call is written to the server log **before** its outcome exists, with the model version, price, probability, ranges and best guess.
- Outcomes are scored automatically at the deadline. There is no manual editing and no backfill.
- The public record **restarted on October 8, 2026 at 7 PM CT** when the current models went live. Older models' calls are archived and not counted, so the record grades only what users see.
- The scorecard shows how often the price landed in range, how often the best guess was right, and the current streak, each with an honest note on the odds.

## 7. Money flows

| Flow | Source | Example reading (Oct 8, 2026) |
|---|---|---|
| XRP on exchanges | Balances of ~800 XRPScan-labeled exchange wallets, read from one XRP Ledger snapshot each hour | ≈ 14.0 billion XRP |
| Whale payments | Completed XRPL payments of 1M+ XRP to or from labeled exchange wallets | Daily in/out totals |
| RLUSD | DefiLlama stablecoin data (XRP Ledger + Ethereum) | ≈ $2.5 billion in circulation |
| Ripple escrow | XRPL escrow objects on Ripple's accounts | 31.4 billion XRP locked; next 1 billion unlocks Oct 31, 7 PM CT |
| US spot XRP ETFs | Flows read from news headlines, clearly labeled as estimates | ≈ $1.7 billion held |

Each block hides itself when its data goes stale, so old numbers never pose as current.

## 8. Crash preparedness

- **Shock monitor:** a banner turns on when XRP moves 3% in 60 minutes or reported forced closes reach $2M in 15 minutes. It clears after two calm hours.
- **What-if panel:** a historical stress scenario scaled to today's volatility.
- **Cascade zones:** estimated clusters of leveraged positions that could speed up a move.
- **Calendar:** XRP Ledger amendment go-live times in Central time, with the 80% / two-week voting rule explained. Also DTCC and Ripple milestones, policy deadlines, escrow unlocks and macro releases.

## 9. Limitations

- Daily crypto direction is close to a coin flip. A 55–60% edge is the realistic ceiling for this kind of data, and it can disappear.
- Exchange, futures and ETF figures are reported snapshots or estimates, not complete totals.
- The models only see market data. They do not know about news before it happens.
- Live results may differ from tests. The public track record is the real test.

## 10. Roadmap

This is version 1 of the paper and the current production model. Expect regular updates as new data sources are tested and the live record grows.


- Test whether leverage and funding history, exchange flows and ETF flows add a real edge, once a few months of data have been collected.
- Better calls on big-move days, where direction tends to be more predictable.
- An opt-in paper-trading bot with a hard kill switch, run only after the public record earns it.

## 11. How it was built

Launch Lab was designed and directed by Zach Riehn and built with AI coding agents (Anthropic's Claude and OpenAI's Codex). Every claim in the product was checked against independent recomputation from raw exchange data, and the site was audited by several AI reviewers.

---

**Try it:** [cocoeatsai.com/area4](https://cocoeatsai.com/area4/) · **About the builder / hire me:** [cocoeatsai.com/about](https://cocoeatsai.com/about/)

© 2026 Zach Riehn. This paper may be shared with attribution. Launch Lab's code, models and model settings are proprietary and not licensed by this repository. Not financial advice.
