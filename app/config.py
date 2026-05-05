from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("SUMIN_STUDY_DB_PATH", ROOT / "data" / "local" / "study.sqlite"))
CONTENT_ROOT = Path(os.environ.get("SUMIN_STUDY_CONTENT_ROOT", ROOT / "content" / "quadratics" / "items"))
CONCEPT_GRAPH_PATH = ROOT / "content" / "quadratics" / "concept_graph.json"
