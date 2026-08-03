from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import EvidenceItem, Finding, RetentionEvent, RetentionEventType


@dataclass(frozen=True)
class RecommendationConfig:
    min_confidence: float = 0.0
    baseline_impact_seconds: float = 2.8
    action_item_cap: int = 3
    evidence_overlap_bonus: float = 0.18
    evidence_nearest_bonus: float = 0.08
    min_overlap_ratio: float = 0.05


_ACTION_TEMPLATES = {
    RetentionEventType.DROP: {
        "category": "Retention Rescue",
        "recommendation": "Trim the lead-in before this moment and deliver a stronger segment transition.",
        "limitation": "Without frame-level video features, this is text-based timing guidance only.",
    },
    RetentionEventType.SPIKE: {
        "category": "Momentum Amplify",
        "recommendation": "Duplicate this energy: add a visual callback + subtitle pattern inside adjacent sections.",
        "limitation": "Could overcorrect if the audience spike is topic-specific rather than style-specific.",
    },
    RetentionEventType.EXIT: {
        "category": "Retention Save",
        "recommendation": "Insert one tight re-hook and CTA bridge before this interval.",
        "limitation": "Audience intent varies; this fix may help viewers who left but not all cohorts.",
    },
    RetentionEventType.REWATCH: {
        "category": "Rewatch Capture",
        "recommendation": "Turn this into a micro-structure marker so the viewer is led back intentionally.",
        "limitation": "This can over-constrain pacing if your script uses legitimate callbacks.",
    },
}

_ACTION_ITEMS = {
    RetentionEventType.DROP: [
        "Cut 1-2 seconds before the drop marker, then tighten sentence cadence.",
        "Move visual emphasis to the strongest anchor line in this range.",
        "Add a 1-line promise for the next section at drop start.",
    ],
    RetentionEventType.SPIKE: [
        "Re-use this punchline tone in the intro or transition.",
        "Add matching graphics/sfx at the same pacing interval.",
        "Create a reusable title card for this winning pattern.",
    ],
    RetentionEventType.EXIT: [
        "Add a short re-hook 0.7-1.2 seconds before start_seconds.",
        "Insert a visual change 1 second before start_seconds.",
        "End with a concrete benefit promise for the next moment.",
    ],
    RetentionEventType.REWATCH: [
        "Label this zone as a named segment and reintroduce it once.",
        "Use a visual flag + subtitles cue to clarify intent.",
        "Add a one-line transition to preserve coherence after revisiting this content.",
    ],
}


def _event_payload(event: RetentionEvent) -> dict[str, Any]:
    return {
        "start_seconds": float(event.start_seconds),
        "end_seconds": float(event.end_seconds),
        "duration_seconds": float(max(0.001, event.end_seconds - event.start_seconds)),
        "score": float(event.score),
        "severity": float(event.severity),
        "type": event.type.value,
    }


def _evidence_bonus(evidence_items: list[EvidenceItem]) -> float:
    if not evidence_items:
        return 0.0
    bonus = 0.0
    source_weights = {
        "transcript_overlap": 1.0,
        "transcript_nearest": 0.8,
        "transcript_outside_window": 0.4,
        "transcript_missing": 0.0,
    }
    for item in evidence_items:
        weight = source_weights.get(item.kind, 0.2)
        bonus = max(bonus, min(0.25, weight * 0.2))
    return bonus


def build_findings(
    events: list[RetentionEvent],
    evidence_items: list[EvidenceItem],
    cfg: RecommendationConfig | None = None,
) -> list[Finding]:
    cfg = cfg or RecommendationConfig()
    evidence_by_event: dict[str, list[EvidenceItem]] = {}
    for item in evidence_items:
        for event_id in item.event_ids:
            evidence_by_event.setdefault(event_id, []).append(item)

    findings: list[Finding] = []
    templates = _ACTION_TEMPLATES
    action_items = _ACTION_ITEMS
    for idx, event in enumerate(events):
        event_evidence = evidence_by_event.get(event.id, [])
        evidence_bonus = _evidence_bonus(event_evidence)
        overlap_ratio = 0.0
        if event_evidence:
            raw = event_evidence[0].metadata.get("transcript_match_ratio", 0.0)
            overlap_ratio = float(raw or 0.0)
        confidence = min(0.99, (event.score * 0.72) + (event.severity * 0.22) + evidence_bonus)
        if confidence < cfg.min_confidence:
            continue
        if overlap_ratio < cfg.min_overlap_ratio and event_evidence:
            confidence *= 0.95

        tpl = templates[event.type]
        evid_snips = [str(item.value or "").strip() for item in event_evidence if item.value]
        top_snip = evid_snips[0] if evid_snips else "No direct transcript evidence available."
        event_payload = _event_payload(event)
        duration_seconds = event_payload["duration_seconds"]
        estimated_impact_seconds = round(cfg.baseline_impact_seconds + (duration_seconds * 0.35 * event.severity), 3)

        findings.append(
            Finding(
                id=f"finding_{event.id}_{idx}",
                run_id=event.run_id,
                category=tpl["category"],
                start_seconds=event.start_seconds,
                end_seconds=event.end_seconds,
                severity=event.severity,
                confidence=round(confidence, 4),
                estimated_impact_seconds=estimated_impact_seconds,
                rationale=(
                    f"{event.type.value} event with score={event.score:.3f}, severity={event.severity:.3f}, "
                    f"duration={duration_seconds:.3f}s and evidence kind={event_evidence[0].kind if event_evidence else 'none'}."
                ),
                observation=(
                    f"At {event.start_seconds:.2f}-{event.end_seconds:.2f}s, retention shifts according to "
                    f"{event.type.value} pattern ({top_snip[:140]})."
                ),
                recommendation=tpl["recommendation"],
                limitation=tpl["limitation"],
                action_items=action_items[event.type][: cfg.action_item_cap],
                evidence_ids=[item.id for item in event_evidence] or [f"missing_evidence_{event.id}"],
            )
        )

    findings.sort(key=lambda item: (item.category, -item.confidence, item.start_seconds))
    return findings
