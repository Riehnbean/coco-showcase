#!/usr/bin/env python3
"""
discover-models.py — Layer 2 of the CoCo meta-AI system.

Polls AI provider APIs, diffs the results against model-registry.json, and reports
(or applies) updates. Default mode is REPORT-ONLY — owner stays in control per the
Vision decision principles. Pass --apply to actually write changes.

Usage:
    python discover-models.py                # report-only, OpenRouter only
    python discover-models.py --apply        # write new models into the registry
    python discover-models.py --all          # also include other providers (stubs for now)
    python discover-models.py --help

Schedule (Windows Task Scheduler):
    Run on your preferred schedule after reviewing report-only output.

What it does today (v0.1):
    - Hits openrouter.ai/api/v1/models
    - Compares model IDs against the registry
    - Identifies: NEW (not in registry), REMOVED (in registry but not in API), DENIED (status: deny-listed; ignored)
    - In --apply mode: appends NEW entries with current_status='not-yet-evaluated', marks
      REMOVED entries as current_status='deprecated', updates last_full_refresh timestamp

What it does NOT do yet:
    - Quality evaluation (that's Layer 3 — scrape LMSYS/HF leaderboards)
    - Auto-promotion (that's Layer 4)
    - Capability classification beyond a heuristic guess (see classify_capabilities())

Requires: Python 3.8+ and `requests` library (pip install requests).
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.stderr.write(
        "ERROR: This script requires `requests`. Install with:\n"
        "    pip install requests\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR / "model-registry.json"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
HTTP_TIMEOUT_SEC = 30


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

CAPABILITY_KEYWORDS = {
    "code": ["code", "coder", "starcoder", "deepcode", "instruct"],
    "reason": ["reason", "thinking", "r1", "o1", "o3", "claude-opus", "gpt-4"],
    "creative": ["creative", "llama", "mistral", "story", "writer"],
    "search": ["sonar", "search", "perplexity"],
    "image": ["dall", "image", "vision", "stable-diffusion", "flux", "imagen"],
    "video": ["video", "veo", "sora"],
    "voice": ["voice", "tts", "whisper", "audio"],
    "embedding": ["embed", "embedding"],
}


def classify_capabilities(model_id: str, model_meta: dict) -> list[str]:
    """Best-effort capability tagging based on model id + provider metadata.

    NOT authoritative. Layer 3 (evaluation) will refine these. For now we want
    a reasonable default so the registry is useful out of the box.
    """
    mid = model_id.lower()
    caps = set()

    # Default: anything chat-y is at least 'simple'
    if any(k in mid for k in ["chat", "instruct", "gpt", "claude", "gemini", "llama", "mistral", "deepseek", "qwen"]):
        caps.add("simple")

    # Keyword matching across categories
    for cap, keywords in CAPABILITY_KEYWORDS.items():
        if any(k in mid for k in keywords):
            caps.add(cap)

    # If OpenRouter exposes modality info, use it
    modality = (model_meta.get("architecture", {}) or {}).get("modality", "")
    if "image" in modality:
        caps.add("image")
    if "audio" in modality:
        caps.add("voice")

    return sorted(caps) if caps else ["simple"]


def free_tier_status_for_openrouter(model_id: str, pricing: dict) -> str:
    """OpenRouter ':free' suffix means shared global rate-limit pool."""
    if model_id.endswith(":free"):
        return "shared_pool"
    prompt_cost = pricing.get("prompt", "0")
    if prompt_cost in ("0", 0, "0.0", 0.0):
        return "shared_pool"  # paid model listed at 0 = shared free pool
    return "none"


# ---------------------------------------------------------------------------
# Provider: OpenRouter
# ---------------------------------------------------------------------------

def fetch_openrouter_models() -> list[dict]:
    """Returns OpenRouter's full model catalog as a list of normalized dicts."""
    print(f"  GET {OPENROUTER_MODELS_URL} ...", end=" ", flush=True)
    try:
        r = requests.get(OPENROUTER_MODELS_URL, timeout=HTTP_TIMEOUT_SEC)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"FAILED: {e}")
        return []
    data = r.json()
    models = data.get("data", [])
    print(f"got {len(models)} models")

    normalized = []
    for m in models:
        model_id = m.get("id", "")
        if not model_id:
            continue
        pricing = m.get("pricing", {}) or {}
        try:
            input_cost_per_token = float(pricing.get("prompt", 0) or 0)
            output_cost_per_token = float(pricing.get("completion", 0) or 0)
        except (TypeError, ValueError):
            input_cost_per_token = output_cost_per_token = None

        normalized.append({
            "provider": "openrouter",
            "model_id": model_id,
            "display_name": m.get("name") or model_id,
            "capabilities": classify_capabilities(model_id, m),
            "cost_per_million_input_tokens_usd": (input_cost_per_token * 1_000_000) if input_cost_per_token is not None else None,
            "cost_per_million_output_tokens_usd": (output_cost_per_token * 1_000_000) if output_cost_per_token is not None else None,
            "free_tier_status": free_tier_status_for_openrouter(model_id, pricing),
            "rate_limit_notes": "OpenRouter; check live for per-model details." if not model_id.endswith(":free") else "OpenRouter shared global free-tier pool. Aggressive throttling.",
            "quality_score_by_capability": None,
            "reliability_score": None,
            "last_tested": None,
            "current_status": "not-yet-evaluated",
            "currently_assigned_routes": [],
            "notes": "Auto-discovered. Capabilities are heuristic; refine with evaluation.",
        })
    return normalized


# ---------------------------------------------------------------------------
# Provider stubs (to be filled in as needed)
# ---------------------------------------------------------------------------

def fetch_anthropic_models() -> list[dict]:
    """Stub. Anthropic models API requires an API key. Skipped for now."""
    print("  Anthropic: stub (requires API key — implement when needed)")
    return []


def fetch_openai_models() -> list[dict]:
    """Stub. OpenAI models API requires an API key. Skipped for now."""
    print("  OpenAI: stub (requires API key — implement when needed)")
    return []


def fetch_google_models() -> list[dict]:
    """Stub. Google AI Studio models API requires a key. Skipped for now."""
    print("  Google AI Studio: stub (implement when needed)")
    return []


def fetch_ollama_library() -> list[dict]:
    """Stub. Ollama library has no JSON API — would need to HTML-scrape ollama.com/library."""
    print("  Ollama Library: stub (HTML scrape — implement when local Ollama is in scope)")
    return []


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        sys.stderr.write(f"ERROR: registry not found at {REGISTRY_PATH}\n")
        sys.exit(2)
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg: dict) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Diff and merge
# ---------------------------------------------------------------------------

def diff_and_report(registry: dict, discovered: list[dict]) -> dict:
    """Returns a dict with 'new', 'removed', 'unchanged' lists of model_ids.

    Discovery here is OpenRouter-scoped for now: we only compare OpenRouter models
    in the registry against OpenRouter results. Other providers are stub-only.
    """
    discovered_ids = {m["model_id"] for m in discovered}
    discovered_by_id = {m["model_id"]: m for m in discovered}

    # Existing OpenRouter models in registry (skip deny-listed; we don't want to re-add tombstones)
    existing = {
        m["model_id"]: m
        for m in registry.get("models", [])
        if m.get("provider") == "openrouter"
    }
    existing_active_ids = {mid for mid, m in existing.items() if m.get("current_status") != "deny-listed"}

    new_ids = sorted(discovered_ids - set(existing.keys()))
    removed_ids = sorted(existing_active_ids - discovered_ids)
    unchanged_ids = sorted(discovered_ids & existing_active_ids)

    return {
        "new": new_ids,
        "removed": removed_ids,
        "unchanged": unchanged_ids,
        "discovered_by_id": discovered_by_id,
        "existing": existing,
    }


def apply_diff(registry: dict, diff: dict) -> int:
    """Mutates registry in place. Returns number of changes applied."""
    changes = 0
    discovered = diff["discovered_by_id"]
    existing = diff["existing"]

    # Append new models
    for mid in diff["new"]:
        registry["models"].append(discovered[mid])
        changes += 1

    # Mark removed models as deprecated
    for m in registry.get("models", []):
        if m.get("provider") == "openrouter" and m["model_id"] in diff["removed"]:
            if m.get("current_status") != "deprecated":
                m["current_status"] = "deprecated"
                m.setdefault("notes", "")
                m["notes"] = (m.get("notes") or "") + " [Auto-marked deprecated by discover-models.py on " + datetime.now(timezone.utc).strftime("%Y-%m-%d") + "]"
                changes += 1

    registry["last_full_refresh"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return changes


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes to the registry. Default is report-only.")
    parser.add_argument("--all", action="store_true", help="Poll all provider stubs, not just OpenRouter.")
    args = parser.parse_args()

    print(f"CoCo — discover-models.py — {'APPLY' if args.apply else 'REPORT-ONLY'} mode")
    print(f"Registry: {REGISTRY_PATH}")
    print()

    print("Fetching:")
    discovered = fetch_openrouter_models()
    if args.all:
        discovered += fetch_anthropic_models()
        discovered += fetch_openai_models()
        discovered += fetch_google_models()
        discovered += fetch_ollama_library()

    if not discovered:
        print("\nNo models returned. Aborting.")
        return 1

    print()
    registry = load_registry()
    diff = diff_and_report(registry, discovered)

    print("=" * 60)
    print(f"OpenRouter diff:")
    print(f"  Already known: {len(diff['unchanged'])}")
    print(f"  NEW:           {len(diff['new'])}")
    print(f"  REMOVED:       {len(diff['removed'])}")
    print("=" * 60)

    if diff["new"]:
        print("\nNEW models discovered:")
        for mid in diff["new"][:50]:
            m = diff["discovered_by_id"][mid]
            free = " [FREE]" if m["free_tier_status"] != "none" else ""
            print(f"  + {mid:<55}{free}  caps={','.join(m['capabilities'])}")
        if len(diff["new"]) > 50:
            print(f"  ... and {len(diff['new']) - 50} more (truncated)")

    if diff["removed"]:
        print("\nREMOVED models (in registry but not in API):")
        for mid in diff["removed"][:20]:
            print(f"  - {mid}")
        if len(diff["removed"]) > 20:
            print(f"  ... and {len(diff['removed']) - 20} more (truncated)")

    if not args.apply:
        print()
        print("Report-only mode. Re-run with --apply to write these changes to the registry.")
        return 0

    print()
    print("Applying changes ...")
    n = apply_diff(registry, diff)
    save_registry(registry)
    print(f"  Wrote {n} change(s) to {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
