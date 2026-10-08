#!/usr/bin/env python3
"""
promote-models.py — Layer 4 of the CoCo meta-AI system.

Reads model-registry.json, finds models whose quality score for a given
capability beats the current default for any route, and reports promotion
candidates. Default mode is NOTIFY-ONLY (per Vision decision principle #2:
"Owner stays in control").

Usage:
    python promote-models.py                # list promotion candidates
    python promote-models.py --apply        # [future] swap routes — not implemented yet
    python promote-models.py --capability code   # narrow to one capability

What this does today (v0.1):
    - Loads the registry
    - For each route in route_assignments_current, looks up the current primary model
    - For each capability that route covers, scans all models with quality_score_by_capability
      for that capability
    - Lists any candidates that score higher than the current primary
    - Prints recommendations: "PROMOTE <candidate> for <route> (<score> vs current <score>)"

What it does NOT do yet:
    - Auto-write the route swap into v5.2 (that's the --apply path; future work)
    - Notify via email/Slack (just stdout for now)
    - Consider reliability tradeoffs (a candidate with 90 quality and 20 reliability
      shouldn't beat a 75/95. Composite-scoring logic is a next iteration.)

Today, with only 6 models seeded, you'll see very few candidates. Layer 4 gets
much more interesting once Layer 3's LMSYS/HF scrapers populate scores on the
other 357 models in the registry.
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR / "model-registry.json"


# Reliability floor: never recommend promoting to a model with reliability < this.
# Stops Layer 4 from suggesting flaky free-tier models that score high on quality
# but fail half the time.
RELIABILITY_FLOOR = 50


# Mapping of route name -> primary capability. Matches the Router's classifier.
ROUTE_TO_CAPABILITY = {
    "simple":   "simple",
    "code":     "code",
    "reason":   "reason",
    "research": "research",
    "search":   "search",
    "creative": "creative",
}


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        sys.stderr.write(f"ERROR: registry not found at {REGISTRY_PATH}\n")
        sys.exit(2)
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def get_score(model: dict, capability: str) -> float | None:
    """Return the quality score for a capability, or None if not scored."""
    q = model.get("quality_score_by_capability")
    if not q:
        return None
    return q.get(capability)


def find_model_by_id(registry: dict, model_id: str) -> dict | None:
    for m in registry.get("models", []):
        if m["model_id"] == model_id:
            return m
    return None


def find_promotion_candidates(registry: dict, capability_filter: str | None = None):
    """Yield (route, capability, current_id, current_score, candidate, candidate_score)."""
    route_assignments = registry.get("route_assignments_current", {})

    for route, capability in ROUTE_TO_CAPABILITY.items():
        if capability_filter and capability != capability_filter:
            continue

        # Pull current primary for this route
        route_cfg = route_assignments.get(route)
        if not route_cfg:
            continue
        current_id = (
            route_cfg.get("primary")
            if isinstance(route_cfg, dict) else route_cfg
        )
        if not current_id:
            continue

        current_model = find_model_by_id(registry, current_id)
        current_score = get_score(current_model, capability) if current_model else None

        # Scan all models with a score for this capability
        for m in registry.get("models", []):
            if m["model_id"] == current_id:
                continue
            if m.get("current_status") in ("deny-listed", "deprecated"):
                continue
            cand_score = get_score(m, capability)
            if cand_score is None:
                continue
            if current_score is not None and cand_score <= current_score:
                continue
            # Apply reliability floor
            cand_rel = m.get("reliability_score")
            if cand_rel is not None and cand_rel < RELIABILITY_FLOOR:
                continue
            yield {
                "route": route,
                "capability": capability,
                "current_id": current_id,
                "current_score": current_score,
                "current_reliability": current_model.get("reliability_score") if current_model else None,
                "candidate_id": m["model_id"],
                "candidate_score": cand_score,
                "candidate_reliability": cand_rel,
                "candidate_status": m.get("current_status"),
            }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="[Not implemented yet] Auto-swap routes for accepted promotions.")
    parser.add_argument("--capability", type=str, default=None, help="Narrow to one capability (simple|code|reason|research|search|creative).")
    args = parser.parse_args()

    print(f"CoCo — promote-models.py (notify-only mode)")
    print(f"Registry: {REGISTRY_PATH}")
    print(f"Reliability floor for promotions: {RELIABILITY_FLOOR}")
    print()

    registry = load_registry()

    # Stats on how much scored data we have to work with
    total = len(registry.get("models", []))
    scored = sum(1 for m in registry.get("models", []) if m.get("quality_score_by_capability"))
    print(f"Registry: {total} models total, {scored} with quality scores")
    print()

    candidates = list(find_promotion_candidates(registry, capability_filter=args.capability))

    if not candidates:
        print("No promotion candidates found.")
        print()
        if scored < 20:
            print("Note: only", scored, "models have quality scores. Layer 4 gets useful")
            print("when Layer 3's LMSYS / HF scrapers populate scores on more models.")
        return 0

    print(f"Found {len(candidates)} promotion candidate(s):")
    print()
    for c in candidates:
        delta = c["candidate_score"] - (c["current_score"] or 0)
        print(f"  PROMOTE: {c['candidate_id']}")
        print(f"    Route: {c['route']}  (capability: {c['capability']})")
        print(f"    Current: {c['current_id']}  score={c['current_score']}  reliability={c['current_reliability']}")
        print(f"    Candidate: score={c['candidate_score']} (+{delta:.0f})  reliability={c['candidate_reliability']}  status={c['candidate_status']}")
        if c["candidate_status"] == "not-yet-evaluated":
            print(f"    WARN: candidate has not been independently evaluated yet — score is heuristic only.")
        print()

    if args.apply:
        print("--apply is not implemented yet. This is notify-only mode.")
        print("To accept a promotion manually: edit model-registry.json's route_assignments_current,")
        print("then PUT the corresponding model swap into v5.2 in n8n.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
