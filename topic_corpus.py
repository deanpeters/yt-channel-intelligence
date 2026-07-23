#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import yaml

from config import LLM_MODEL
from phases.topic_export import export_corpus
from phases.topic_enrich import enrich_corpus
from phases.topic_retrieval import build_index, query_index


def _print_hits(hits: list[dict]) -> None:
    for number, hit in enumerate(hits, start=1):
        metadata = hit["metadata"]
        print(f"\n{number}. {metadata['title']} — {metadata['start_seconds']}s")
        print(f"   {hit['deep_link']}")
        if metadata.get("summary"):
            print(f"   {metadata['summary']}")
        print(f"   {hit['text'][:500].strip()}")
        mechanisms = metadata.get("failure_mechanisms")
        if mechanisms:
            print(f"   Labels: {mechanisms}")


def _evaluate(config_path: str, questions_path: str, output_path: str) -> None:
    with open(questions_path, encoding="utf-8") as f:
        questions = (yaml.safe_load(f) or {}).get("questions", [])

    lines = [
        "# Business Failures Retrieval Evaluation",
        "",
        "This is a mechanical retrieval check, not a truth evaluation.",
        "A strict pass requires all expected cases and all expected mechanism labels "
        "to appear in the diversified top six. Questions without expected mechanisms "
        "are scored on case coverage only.",
        "",
    ]
    case_passes = 0
    strict_passes = 0
    for number, item in enumerate(questions, start=1):
        hits = query_index(config_path, item["question"])
        found_cases = {hit["metadata"]["video_id"] for hit in hits}
        expected_cases = set(item.get("expected_cases", []))
        case_pass = expected_cases.issubset(found_cases) if expected_cases else True
        case_passes += int(case_pass)

        found_mechanisms = set()
        for hit in hits:
            found_mechanisms.update(
                value
                for value in hit["metadata"].get(
                    "failure_mechanisms",
                    "",
                ).split(",")
                if value
            )
        expected_mechanisms = set(item.get("expected_mechanisms", []))
        mechanism_matches = sorted(found_mechanisms & expected_mechanisms)
        mechanism_pass = (
            expected_mechanisms.issubset(found_mechanisms)
            if expected_mechanisms
            else True
        )
        strict_pass = case_pass and mechanism_pass
        strict_passes += int(strict_pass)

        lines += [
            f"## {number}. {item['question']}",
            "",
            f"**Strict result:** {'PASS' if strict_pass else 'FAIL'}",
            "",
            f"**Case coverage:** {len(found_cases & expected_cases)}/"
            f"{len(expected_cases)}",
            "",
            (
                f"**Mechanism coverage:** {len(mechanism_matches)}/"
                f"{len(expected_mechanisms)}"
                if expected_mechanisms
                else "**Mechanism coverage:** not scored"
            ),
            "",
            f"**Expected mechanisms found:** "
            f"{', '.join(mechanism_matches) or 'none'}",
            "",
        ]
        for hit in hits:
            metadata = hit["metadata"]
            excerpt = hit["text"].replace("\n", " ")[:260]
            lines += [
                f"- [{metadata['title']} at {metadata['start_seconds']}s]"
                f"({hit['deep_link']}) — {excerpt}",
            ]
        lines.append("")

    lines[4:4] = [
        f"**Strict score:** {strict_passes}/{len(questions)}",
        "",
        f"**Complete case-coverage score:** {case_passes}/{len(questions)}",
        "",
    ]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Evaluation ready: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Enrich, index, and query an experimental topical corpus."
    )
    parser.add_argument(
        "--config",
        default="topics/business-failures.yaml",
        help="Topic corpus configuration file.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    enrich = subparsers.add_parser("enrich")
    enrich.add_argument("--label-with-llm", action="store_true")
    enrich.add_argument(
        "--relabel-all",
        action="store_true",
        help="Reclassify existing passages even when the taxonomy version is unchanged.",
    )
    enrich.add_argument("--model", default=LLM_MODEL)

    subparsers.add_parser("index")
    subparsers.add_parser("export")

    query = subparsers.add_parser("query")
    query.add_argument("question")
    query.add_argument("--results", type=int, default=6)

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument(
        "--questions",
        default="evaluations/business-failures-questions.yaml",
    )
    evaluate.add_argument(
        "--output",
        default="reports/topics/business-failures-retrieval-evaluation.md",
    )

    args = parser.parse_args()
    if args.command == "enrich":
        path, stats = enrich_corpus(
            args.config,
            label_with_llm=args.label_with_llm,
            model=args.model,
            relabel_all=args.relabel_all,
        )
        print(f"Enrichment ready: {path}")
        print(json.dumps(stats, indent=2))
    elif args.command == "index":
        path, count = build_index(args.config)
        print(f"Index ready: {path} ({count} passages)")
    elif args.command == "export":
        path, stats = export_corpus(args.config)
        print(f"Portable exports ready: {path}")
        print(json.dumps(stats, indent=2))
    elif args.command == "query":
        _print_hits(query_index(args.config, args.question, limit=args.results))
    elif args.command == "evaluate":
        _evaluate(args.config, args.questions, args.output)


if __name__ == "__main__":
    main()
