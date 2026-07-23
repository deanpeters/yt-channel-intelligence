import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from phases.topic_enrich import load_topic_config


MECHANISM_QUERY_TERMS = {
    "path_dependence": (
        "early structural",
        "later adaptation",
        "path dependence",
        "locked in",
        "legacy choice",
    ),
    "financial_leverage": ("debt", "leverage", "borrow"),
    "cost_structure_mismatch": (
        "cost structure",
        "fixed costs",
        "operating leverage",
    ),
    "feedback_suppression": (
        "warning ignored",
        "warnings ignored",
        "feedback suppressed",
        "suppressed feedback",
        "inconvenient feedback",
        "overruled",
    ),
    "normalization_of_deviance": (
        "normalization of deviance",
        "accepted risk",
        "warning signs",
    ),
    "short_term_optimization": (
        "short-term",
        "short term",
        "near-term",
        "quarterly",
    ),
    "incentive_misalignment": ("incentive", "rewarded the wrong"),
    "unclear_positioning": (
        "incompatible strategic",
        "stuck between",
        "strategic position",
        "positioning",
    ),
    "mission_loss": (
        "original mission",
        "mission failure",
        "fails to define another",
        "institutional mission",
    ),
    "capability_erosion": (
        "focused competitors",
        "incumbent's weakness",
        "incumbent weakness",
        "lost capability",
    ),
    "failed_transformation": (
        "turnaround",
        "replacement strategies",
        "attempted",
        "work or fail",
    ),
    "market_or_demographic_shift": (
        "corporate decline",
        "market shift",
        "demographic",
    ),
    "channel_or_platform_dependency": (
        "platform dependence",
        "platform dependency",
        "channel dependence",
        "cable distribution",
        "gatekeeper",
    ),
    "adverse_selection": ("adverse selection", "best participants stopped"),
    "success_induced_obsolescence": (
        "success-induced obsolescence",
        "success induced obsolescence",
        "made itself less necessary",
        "own success",
    ),
    "acquisition_or_integration_failure": (
        "acquisition failure",
        "integration failure",
        "bad acquisition",
        "overpaid acquisition",
    ),
}

CAUSAL_ROLE_QUERY_TERMS = {
    "warning_signal": ("warning sign", "warning signs", "before the visible"),
    "response": ("turnaround", "replacement", "response", "attempted"),
    "structural_constraint": ("structural choice", "structural choices"),
}

CASE_ROLE_QUERY_TERMS = {
    "turnaround_counterexample": (
        "turnaround counterexample",
        "successful turnaround",
        "recovered",
        "focused path",
    ),
    "resilience_counterexample": (
        "resilience counterexample",
        "successful adaptation",
        "avoided decline",
    ),
    "partial_recovery": (
        "partial recovery",
        "smaller revival",
        "smaller or more focused path",
    ),
}


def infer_query_intent(question: str) -> dict[str, list[str]]:
    normalized = " ".join(question.lower().replace("’", "'").split())
    return {
        "failure_mechanisms": [
            label
            for label, terms in MECHANISM_QUERY_TERMS.items()
            if any(term in normalized for term in terms)
        ],
        "causal_roles": [
            label
            for label, terms in CAUSAL_ROLE_QUERY_TERMS.items()
            if any(term in normalized for term in terms)
        ],
        "case_roles": [
            label
            for label, terms in CASE_ROLE_QUERY_TERMS.items()
            if any(term in normalized for term in terms)
        ],
    }


def resolve_case_tokens(config: dict, tokens: list[str]) -> list[str]:
    """Map --case tokens to video IDs. A token may be a video ID or a
    case-insensitive substring of a subject (e.g. "pizza" -> Pizza Hut)."""
    cases = config.get("cases", {})
    resolved = []
    unmatched = []
    for token in tokens:
        if token in cases:
            resolved.append(token)
            continue
        needle = token.lower()
        matches = [
            video_id
            for video_id, case in cases.items()
            if needle in case.get("subject", "").lower()
        ]
        if matches:
            resolved.extend(matches)
        else:
            unmatched.append(token)
    if unmatched:
        raise ValueError(
            "No case matched: " + ", ".join(unmatched)
        )
    return list(dict.fromkeys(resolved))


def build_scope_filter(
    *,
    industries: list[str] | None = None,
    case_roles: list[str] | None = None,
    video_ids: list[str] | None = None,
    playlist_min: int | None = None,
    playlist_max: int | None = None,
) -> dict | None:
    """Build a ChromaDB `where` filter from retrieval-scope options.

    Returns None when no scope is requested, a single clause when exactly one
    dimension is set, and an `$and` of clauses otherwise."""
    clauses = []
    if industries:
        clauses.append({"industry": {"$in": list(industries)}})
    if case_roles:
        clauses.append({"case_role": {"$in": list(case_roles)}})
    if video_ids:
        clauses.append({"video_id": {"$in": list(video_ids)}})
    if playlist_min is not None:
        clauses.append({"playlist_index": {"$gte": playlist_min}})
    if playlist_max is not None:
        clauses.append({"playlist_index": {"$lte": playlist_max}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _load_chromadb():
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "Topical retrieval needs ChromaDB. Run: "
            "python3 -m pip install chromadb"
        ) from exc
    return chromadb


def _metadata(passage: dict) -> dict:
    labels = passage["labels"]
    case = passage["case"]
    return {
        "video_id": passage["video_id"],
        "title": passage["title"],
        "subject": case["subject"],
        "case_role": case.get("case_role", "unspecified"),
        "subject_type": case["subject_type"],
        "industry": case["industry"],
        "playlist_index": passage.get("playlist_index", 0),
        "start_seconds": passage["start_seconds"],
        "end_seconds": passage["end_seconds"],
        "youtube_url": passage["youtube_url"],
        "taxonomy_version": passage["taxonomy_version"],
        "transcript_source": passage["transcript_source"],
        "causal_roles": ",".join(labels.get("causal_roles") or []),
        "failure_mechanisms": ",".join(labels.get("failure_mechanisms") or []),
        "actors": ",".join(labels.get("actors") or []),
        "evidence_types": ",".join(labels.get("evidence_types") or []),
        "epistemic_status": labels["epistemic_status"],
        "summary": labels["summary"],
        "case_failure_mechanisms": ",".join(case.get("failure_mechanisms") or []),
        "failure_states": ",".join(case.get("failure_states") or []),
    }


def build_index(config_path: str) -> tuple[str, int]:
    chromadb = _load_chromadb()
    config = load_topic_config(config_path)
    workspace = Path(config["workspace"])
    passages_path = workspace / "enrichment" / "passages.jsonl"
    passages = [
        json.loads(line)
        for line in passages_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    passages = [
        passage
        for passage in passages
        if passage["include_in_index"]
        and passage["labels"]["review_status"] != "unlabeled"
    ]
    if not passages:
        raise RuntimeError("No labeled, indexable passages found. Run enrich first.")

    model = SentenceTransformer(config["embedding_model"])
    documents = [passage["text"] for passage in passages]
    embedding_texts = [
        "\n".join([
            passage["labels"]["summary"],
            "Causal roles: "
            + ", ".join(passage["labels"]["causal_roles"]),
            "Failure mechanisms: "
            + ", ".join(passage["labels"]["failure_mechanisms"]),
            "Actors: " + ", ".join(passage["labels"]["actors"]),
            passage["text"],
        ])
        for passage in passages
    ]
    embeddings = model.encode(
        embedding_texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()

    index_path = workspace / "index" / "chroma_db"
    index_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(index_path))
    collection_name = config["collection_name"]
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(
        collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": config["embedding_model"],
            "taxonomy_version": config["taxonomy_version"],
        },
    )
    collection.add(
        ids=[passage["passage_id"] for passage in passages],
        documents=documents,
        metadatas=[_metadata(passage) for passage in passages],
        embeddings=embeddings,
    )
    return str(index_path), collection.count()


def _mmr_select(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    metadatas: list[dict],
    limit: int,
    lambda_mult: float = 0.72,
    max_per_video: int = 2,
) -> list[int]:
    selected = []
    remaining = list(range(len(metadatas)))
    per_video = {}
    relevance = candidate_embeddings @ query_embedding

    while remaining and len(selected) < limit:
        best_index = None
        best_score = float("-inf")
        for index in remaining:
            video_id = metadatas[index]["video_id"]
            if per_video.get(video_id, 0) >= max_per_video:
                continue
            diversity = (
                max(candidate_embeddings[index] @ candidate_embeddings[j] for j in selected)
                if selected
                else 0.0
            )
            score = lambda_mult * relevance[index] - (1 - lambda_mult) * diversity
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is None:
            break
        selected.append(best_index)
        remaining.remove(best_index)
        video_id = metadatas[best_index]["video_id"]
        per_video[video_id] = per_video.get(video_id, 0) + 1
    return selected


def _split_metadata_labels(metadata: dict, key: str) -> set[str]:
    return {
        value
        for value in metadata.get(key, "").split(",")
        if value
    }


def _hybrid_relevance(
    semantic_relevance: np.ndarray,
    metadatas: list[dict],
    intent: dict[str, list[str]],
) -> np.ndarray:
    scores = semantic_relevance.astype(float).copy()
    wanted_mechanisms = set(intent["failure_mechanisms"])
    wanted_roles = set(intent["causal_roles"])
    wanted_case_roles = set(intent.get("case_roles", []))
    for index, metadata in enumerate(metadatas):
        passage_mechanisms = _split_metadata_labels(
            metadata,
            "failure_mechanisms",
        )
        case_mechanisms = _split_metadata_labels(
            metadata,
            "case_failure_mechanisms",
        )
        passage_roles = _split_metadata_labels(metadata, "causal_roles")
        case_role = metadata.get("case_role", "")
        scores[index] += 0.18 * min(
            2,
            len(wanted_mechanisms & passage_mechanisms),
        )
        scores[index] += 0.05 * min(
            2,
            len(wanted_mechanisms & case_mechanisms),
        )
        scores[index] += 0.14 * min(1, len(wanted_roles & passage_roles))
        if case_role in wanted_case_roles:
            scores[index] += 0.22
    return scores


def _hybrid_select(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    metadatas: list[dict],
    intent: dict[str, list[str]],
    limit: int,
    lambda_mult: float = 0.78,
    max_per_video: int = 2,
) -> list[int]:
    semantic_relevance = candidate_embeddings @ query_embedding
    relevance = _hybrid_relevance(
        semantic_relevance,
        metadatas,
        intent,
    )
    selected = []
    remaining = set(range(len(metadatas)))
    per_video = {}

    # Reserve one strong passage-level match for each inferred mechanism. This
    # preserves label coverage without requiring the caller to know a case ID.
    for mechanism in intent["failure_mechanisms"]:
        eligible = [
            index
            for index in remaining
            if mechanism
            in _split_metadata_labels(
                metadatas[index],
                "failure_mechanisms",
            )
            and per_video.get(metadatas[index]["video_id"], 0)
            < max_per_video
        ]
        if not eligible or len(selected) >= limit:
            continue
        best = max(eligible, key=lambda index: relevance[index])
        selected.append(best)
        remaining.remove(best)
        video_id = metadatas[best]["video_id"]
        per_video[video_id] = per_video.get(video_id, 0) + 1

    for case_role in intent.get("case_roles", []):
        eligible = [
            index
            for index in remaining
            if metadatas[index].get("case_role") == case_role
            and per_video.get(metadatas[index]["video_id"], 0)
            < max_per_video
        ]
        if not eligible or len(selected) >= limit:
            continue
        best = max(eligible, key=lambda index: relevance[index])
        selected.append(best)
        remaining.remove(best)
        video_id = metadatas[best]["video_id"]
        per_video[video_id] = per_video.get(video_id, 0) + 1

    while remaining and len(selected) < limit:
        best_index = None
        best_score = float("-inf")
        for index in remaining:
            video_id = metadatas[index]["video_id"]
            if per_video.get(video_id, 0) >= max_per_video:
                continue
            diversity = (
                max(
                    candidate_embeddings[index] @ candidate_embeddings[j]
                    for j in selected
                )
                if selected
                else 0.0
            )
            score = (
                lambda_mult * relevance[index]
                - (1 - lambda_mult) * diversity
            )
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is None:
            break
        selected.append(best_index)
        remaining.remove(best_index)
        video_id = metadatas[best_index]["video_id"]
        per_video[video_id] = per_video.get(video_id, 0) + 1
    return selected


def query_index(
    config_path: str,
    question: str,
    limit: int = 6,
    candidate_count: int | None = None,
    scope: dict | None = None,
) -> list[dict]:
    chromadb = _load_chromadb()
    config = load_topic_config(config_path)
    workspace = Path(config["workspace"])
    client = chromadb.PersistentClient(
        path=str(workspace / "index" / "chroma_db")
    )
    collection = client.get_collection(config["collection_name"])
    model = SentenceTransformer(config["embedding_model"])
    intent = infer_query_intent(question)
    query_context = question
    if intent["failure_mechanisms"]:
        query_context += (
            "\nFailure mechanisms: "
            + ", ".join(intent["failure_mechanisms"])
        )
    if intent["causal_roles"]:
        query_context += (
            "\nCausal roles: "
            + ", ".join(intent["causal_roles"])
        )
    if intent["case_roles"]:
        query_context += (
            "\nCase roles: "
            + ", ".join(intent["case_roles"])
        )
    query_embedding = model.encode(
        [query_context],
        normalize_embeddings=True,
    )[0]
    result = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=(
            collection.count()
            if candidate_count is None
            else min(candidate_count, collection.count())
        ),
        where=scope,
        include=["documents", "metadatas", "embeddings", "distances"],
    )
    if not result["ids"][0]:
        return []
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    embeddings = np.asarray(result["embeddings"][0], dtype=float)
    distances = result["distances"][0]
    ids = result["ids"][0]

    selected = _hybrid_select(
        query_embedding,
        embeddings,
        metadatas,
        intent,
        limit=limit,
    )
    hits = []
    for index in selected:
        metadata = metadatas[index]
        separator = "&" if "?" in metadata["youtube_url"] else "?"
        hits.append({
            "passage_id": ids[index],
            "text": documents[index],
            "distance": distances[index],
            "query_intent": intent,
            "metadata": metadata,
            "deep_link": (
                f"{metadata['youtube_url']}{separator}"
                f"t={metadata['start_seconds']}s"
            ),
        })
    return hits
