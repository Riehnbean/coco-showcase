# CoCo showcase · Zach Riehn

Selected, public pieces of **[CoCo](https://cocoeatsai.com)**, a solo-built, multi-provider AI router and research lab. There is also a write-up of **[Launch Lab](https://cocoeatsai.com/area4/)**, the free XRP research dashboard that runs on the same site.

> **Work in progress.** This is the current version of these tools and of the Launch Lab model. They are actively being improved and will change over time. The live site is always the most up-to-date version.

## What's here

| Item | What it is |
|---|---|
| [`LAUNCH-LAB-PAPER.md`](LAUNCH-LAB-PAPER.md) | How Launch Lab works: design principles, forecasting method, how it was tested, measured results, what didn't work, and its limits. Code and model settings are not included. |
| [`discover-models.py`](discover-models.py) | Polls a public AI model catalog, compares it with the registry, and reports new and removed models. Report-only by default. |
| [`evaluate-models.py`](evaluate-models.py) | Scores models per capability (code, reasoning, search, creative and more) from baseline and benchmark inputs. |
| [`promote-models.py`](promote-models.py) | Picks which model serves each route based on scores and reliability, with the owner kept in the loop. |
| [`model-registry.json`](model-registry.json) | Example registry schema, filled with synthetic demo values. |
| [`router.js`](router.js) | The keyword route selector: it sorts a message into translate, summarize, code, search, reason, creative, research or simple. |
| [`workflows/`](workflows/) | Two inactive, credential-free n8n templates: a catalog review and a route-selection preview. |

## How CoCo routes a request

```
message → keyword router → route (code / reason / search / ...) → best model for that route (from the registry) → answer
                                      ▲
         discover → evaluate → promote  (keeps the registry current as new models ship)
```

## Run it

```bash
pip install -r requirements.txt
python discover-models.py          # report-only
python evaluate-models.py --help
python promote-models.py --help
```

The n8n templates import into n8n as inactive workflows and need no credentials.

## Not included

Launch Lab and Trading Lab code, forecasting models and settings, data collectors, private automations and anything tied to accounts or credentials all stay private.

## About

Built by **Zach Riehn**: 9+ years in crypto, former marketing lead for Hoge Finance, B.S. in Mass Communications. Built with AI coding agents (Claude and Codex) under his design and direction.

- Site: [cocoeatsai.com](https://cocoeatsai.com)
- Hire me / contact: [cocoeatsai.com/about](https://cocoeatsai.com/about/)

## License

[PolyForm Noncommercial 1.0.0](LICENSE.md): free to read, learn from and use non-commercially. Commercial use needs written permission.

Required Notice: Copyright 2026 Zach Riehn (https://cocoeatsai.com)

Launch Lab is research and education, not financial advice.
