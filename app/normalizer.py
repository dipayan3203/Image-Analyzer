import json
from typing import Any, Dict, List

try:
    from app.schemas import Analysis, Label
except ImportError:
    from schemas import Analysis, Label


def normalize_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Expect raw to be dict containing analysis block
    if not isinstance(raw, dict):
        raise ValueError("Raw response must be a dict")

    analysis = raw.get("analysis") or {}
    description = analysis.get("description", "")
    labels_raw = analysis.get("labels", [])

    labels: List[Label] = []
    for l in labels_raw:
        name = l.get("name") or l.get("label")
        confidence = float(l.get("confidence", 0.0))
        labels.append(Label(name=name, confidence=confidence))

    # compute overall confidence as average
    if labels:
        avg_conf = sum(l.confidence for l in labels) / len(labels)
    else:
        avg_conf = float(analysis.get("confidence", 0.0))

    analysis_model = Analysis(
        description=description,
        labels=labels,
        confidence=avg_conf,
        data=analysis.get("data")
    )

    normalized = {
        "status": raw.get("status", "success"),
        "analysis": analysis_model.model_dump(exclude_none=True),
        "errors": raw.get("errors", []),
    }
    return normalized
