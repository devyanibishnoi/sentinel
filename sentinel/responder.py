"""Gated auto-responder (TDS-5).

Confidence input is score_population, NOT score_combined (ADR-0007):
entity-deviation was rigorously shown not to improve on population-only,
so the Orchestrator doesn't act on a signal already proven not to help.
Ring membership is a second, independent trigger, not blended into one
number, since ring detection WAS independently validated as real signal.

Non-negotiable (CLAUDE.md): every call to evaluate produces an audit
record, including every detection that resolves to "allow", there is no
code path that skips it.
"""

from dataclasses import dataclass


@dataclass
class Playbook:
    confidence_threshold: float
    exposure_threshold: float  # transaction amount, the exposure proxy


@dataclass
class Decision:
    action: str  # allow | review | decline
    reasoning: str


@dataclass
class AuditRecord:
    transaction_id: str
    entity_id: str
    score_population: float
    ring_cluster_id: str | None
    typology_tag: str | None
    transaction_amount: float
    decision: str
    reasoning: str


class Orchestrator:
    def __init__(self, playbook: Playbook):
        self.playbook = playbook

    def evaluate(self, detection: dict) -> Decision:
        # isinstance check, not "is not None": pandas 3.0's string dtype
        # normalizes BOTH None and NaN into its own internal missing
        # marker, so a cluster id column can't actually hold a literal
        # None, see docs/LEARNING_LOG.md. A real cluster id is always a
        # non-empty string; anything else means "not a ring member."
        is_ring_member = isinstance(detection.get("ring_cluster_id"), str)
        is_high_confidence = detection["score_population"] >= self.playbook.confidence_threshold
        triggered = is_ring_member or is_high_confidence

        if not triggered:
            return Decision(
                "allow",
                "no trigger matched: population score below confidence_threshold, not a ring member",
            )

        trigger_reason = "ring membership" if is_ring_member else "high population score"
        if detection["TransactionAmt"] <= self.playbook.exposure_threshold:
            return Decision("decline", f"{trigger_reason}; exposure within autonomous-action threshold")
        return Decision(
            "review", f"{trigger_reason}; exposure exceeds autonomous-action threshold, routed to human"
        )

    def audit(self, detection: dict, decision: Decision) -> AuditRecord:
        return AuditRecord(
            transaction_id=str(detection["TransactionID"]),
            entity_id=detection["entity_id"],
            score_population=float(detection["score_population"]),
            ring_cluster_id=detection.get("ring_cluster_id"),
            typology_tag=detection.get("typology_tag"),
            transaction_amount=float(detection["TransactionAmt"]),
            decision=decision.action,
            reasoning=decision.reasoning,
        )
