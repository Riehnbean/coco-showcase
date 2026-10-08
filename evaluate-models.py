#!/usr/bin/env python3
"""
evaluate-models.py — Layer 3 of the CoCo meta-AI system.

Updates quality_score_by_capability and reliability_score on entries in
model-registry.json. Three modes:

    --seed       Apply hand-curated baseline scores for the currently active
                 models. Run this once to give the registry meaningful
                 numbers to compare against. Re-run any time you want to
                 update the baselines.

    --lmsys      [STUB] Scrape LMSYS Chatbot Arena leaderboard and import
                 scores. Not implemented yet — placeholder for when we add
                 a real scraper (HTML-heavy site, needs Playwright or similar).

    --hf         [STUB] Pull HuggingFace Open LLM Leaderboard scores.
                 Not implemented yet.

    (no flag)    Report-only: show which models in the registry are missing
                 quality scores and which would be updated by --seed.

Usage:
    python evaluate-models.py
    python evaluate-models.py --seed
    python evaluate-models.py --seed --dry-run

Manual sources for the seed scores below (as of 2026-05-22):
  - lmarena.ai/leaderboard (Arena Elo for chat quality)
  - artificialanalysis.ai (independent benchmarks for code, reasoning, speed)
  - reported provider benchmarks (use with skepticism, they're motivated)

Scores are 0-100 (higher better). reliability_score is empirical (does this
thing actually return a response without erroring?). quality_score_by_capability
is per-capability subjective quality.
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR / "model-registry.json"


# ---------------------------------------------------------------------------
# Seed scores — hand-curated baseline for the currently active models.
# ---------------------------------------------------------------------------
# Format: {model_id: {"quality": {capability: 0-100}, "reliability": 0-100, "source": "where this came from"}}
# Update these manually when better numbers exist; or replace whole entries
# when LMSYS/HF scraping comes online.

SEED_SCORES = {
    "models/gemini-2.5-pro": {
        "quality": {
            "simple": 85,
            "code": 78,
            "reason": 82,
            "research": 88,
            "creative": 75,
            "tool-use": 80,
        },
        "reliability": 75,
        "source": "Manual baseline 2026-05-22. Strong on long context and structured output; hits its 100/day RPD limit fast under testing load.",
    },
    "models/gemini-2.5-flash": {
        "quality": {
            "simple": 78,
            "code": 70,
            "creative": 68,
            "tool-use": 72,
        },
        "reliability": 80,
        "source": "Manual baseline 2026-05-22. Workhorse for fast routes. Occasionally returns markdown-wrapped JSON which is a known parser failure mode.",
    },
    "deepseek/deepseek-v4-flash:free": {
        "quality": {
            "code": 72,
            "reason": 70,
        },
        "reliability": 35,
        "source": "Manual baseline 2026-05-22. Capable when it answers but OpenRouter shared free pool throttles aggressively (~50% fail rate in back-to-back testing).",
    },
    "meta-llama/llama-3.3-70b-instruct:free": {
        "quality": {
            "creative": 76,
        },
        "reliability": 35,
        "source": "Manual baseline 2026-05-22. Witty/sharp when it responds; same shared free pool problem as DeepSeek.",
    },
    "tavily-search-basic": {
        "quality": {
            "search": 85,
        },
        "reliability": 90,
        "source": "Manual baseline 2026-05-22. Designed for AI agents, returns clean sourced results. 1000/mo free per key.",
    },
    "toolWikipedia": {
        "quality": {
            "search": 50,
        },
        "reliability": 95,
        "source": "Manual baseline 2026-05-22. Free and stable but limited to encyclopedic content; weak on current events.",
    },
}


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        sys.stderr.write(f"ERROR: registry not found at {REGISTRY_PATH}\n")
        sys.exit(2)
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(reg: dict) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def report(registry: dict) -> None:
    models = registry.get("models", [])
    scored = [m for m in models if m.get("quality_score_by_capability")]
    unscored = [m for m in models if not m.get("quality_score_by_capability")]

    print(f"Registry: {len(models)} models total")
    print(f"  With quality scores:    {len(scored)}")
    print(f"  Without quality scores: {len(unscored)}")
    print()

    seed_targets = []
    for m in models:
        if m["model_id"] in SEED_SCORES and not m.get("quality_score_by_capability"):
            seed_targets.append(m["model_id"])

    if seed_targets:
        print(f"--seed would populate scores for {len(seed_targets)} model(s):")
        for mid in seed_targets:
            print(f"  + {mid}")
    else:
        print("--seed: nothing to do (all SEED_SCORES entries already populated).")


def apply_seed(registry: dict, dry_run: bool = False) -> int:
    changes = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for m in registry.get("models", []):
        seed = SEED_SCORES.get(m["model_id"])
        if not seed:
            continue
        new_quality = seed["quality"]
        new_reliability = seed["reliability"]
        if m.get("quality_score_by_capability") != new_quality or m.get("reliability_score") != new_reliability:
            print(f"  Updating {m['model_id']}")
            print(f"    quality:     {m.get('quality_score_by_capability')} -> {new_quality}")
            print(f"    reliability: {m.get('reliability_score')} -> {new_reliability}")
            if not dry_run:
                m["quality_score_by_capability"] = new_quality
                m["reliability_score"] = new_reliability
                m["last_tested"] = today
                existing_notes = m.get("notes", "") or ""
                marker = f"[Layer 3 seed score applied {today}: {seed['source']}]"
                if marker not in existing_notes:
                    m["notes"] = (existing_notes + " " + marker).strip()
            changes += 1
    return changes


def stub_lmsys(registry: dict) -> int:
    print("LMSYS leaderboard scraping is not implemented yet.")
    print("Plan: fetch lmarena.ai/leaderboard, parse Arena Elo scores,")
    print("      normalize to 0-100, write to quality_score_by_capability['simple'].")
    print("Implementation needs Playwright/Selenium because the leaderboard is JS-rendered.")
    return 0


def stub_hf(registry: dict) -> int:
    print("HuggingFace Open LLM Leaderboard import is not implemented yet.")
    print("Plan: hit huggingface.co/api/spaces/HuggingFaceH4/open_llm_leaderboard")
    print("      or scrape the leaderboard space directly. Map MMLU/HellaSwag/etc")
    print("      benchmark scores into quality_score_by_capability by capability bucket.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--seed", action="store_true", help="Apply hand-curated baseline scores from SEED_SCORES dict.")
    parser.add_argument("--lmsys", action="store_true", help="[Stub] Scrape LMSYS leaderboard. Not implemented.")
    parser.add_argument("--hf", action="store_true", help="[Stub] Pull HuggingFace leaderboard. Not implemented.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change but don't write.")
    args = parser.parse_args()

    print(f"CoCo — evaluate-models.py")
    print(f"Registry: {REGISTRY_PATH}")
    if args.dry_run:
        print("DRY RUN — no writes will occur.")
    print()

    registry = load_registry()

    if args.lmsys:
        stub_lmsys(registry)
        return 0
    if args.hf:
        stub_hf(registry)
        return 0

    if args.seed:
        print("Applying SEED_SCORES ...")
        changes = apply_seed(registry, dry_run=args.dry_run)
        if changes and not args.dry_run:
            save_registry(registry)
            print(f"\nWrote {changes} update(s) to {REGISTRY_PATH}")
        elif changes:
            print(f"\n[dry-run] Would have written {changes} update(s).")
        else:
            print("\nNo changes needed.")
        return 0

    # Default: report
    report(registry)
    print()
    print("Pass --seed to apply baseline scores, or --lmsys / --hf for the (stub) scrapers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
