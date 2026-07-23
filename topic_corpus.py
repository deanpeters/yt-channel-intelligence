#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import yaml

from config import LLM_MODEL
from phases.topic_export import export_corpus
from phases.topic_enrich import enrich_corpus, load_topic_config
from phases.topic_retrieval import (
    build_index,
    build_scope_filter,
    query_index,
    resolve_case_tokens,
)
from phases.topic_review import (
    apply_review_worksheet,
    build_review_worksheet,
)
from phases.topic_learning import build_learning_layer
from phases.topic_teaching import build_teaching_layer
from phases.topic_pedagogy import evaluate_pedagogy
from phases.topic_synthesis import render_answer_md, synthesize_answer
from phases.topic_corroboration import run_corroboration


def _scope_from_args(args):
    video_ids = None
    if args.case:
        video_ids = resolve_case_tokens(load_topic_config(args.config), args.case)
    return build_scope_filter(
        industries=args.industry,
        case_roles=args.case_role,
        video_ids=video_ids,
        playlist_min=args.playlist_min,
        playlist_max=args.playlist_max,
    )


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
    subparsers.add_parser("learn")
    teach = subparsers.add_parser("teach")
    teach.add_argument("--model", default=LLM_MODEL)

    evaluate_learning = subparsers.add_parser("evaluate-learning")
    evaluate_learning.add_argument(
        "--output",
        default="reports/topics/business-failures-pedagogy-evaluation.md",
    )

    def _add_scope_flags(parser):
        parser.add_argument(
            "--industry",
            action="append",
            metavar="NAME",
            help="Limit to one or more industries (repeatable).",
        )
        parser.add_argument(
            "--case-role",
            action="append",
            metavar="ROLE",
            help="Limit to one or more case roles, e.g. failure (repeatable).",
        )
        parser.add_argument(
            "--case",
            action="append",
            metavar="ID_OR_SUBJECT",
            help="Limit to a video ID or subject substring, e.g. pizza (repeatable).",
        )
        parser.add_argument(
            "--playlist-min",
            type=int,
            help="Limit to playlist positions at or after this index.",
        )
        parser.add_argument(
            "--playlist-max",
            type=int,
            help="Limit to playlist positions at or before this index.",
        )

    query = subparsers.add_parser("query")
    query.add_argument("question")
    query.add_argument("--results", type=int, default=6)
    _add_scope_flags(query)

    answer = subparsers.add_parser("answer")
    answer.add_argument("question")
    answer.add_argument("--results", type=int, default=8)
    answer.add_argument("--model", default=LLM_MODEL)
    answer.add_argument(
        "--output",
        help="Write the answer to this Markdown file instead of stdout.",
    )
    _add_scope_flags(answer)

    corroborate = subparsers.add_parser("corroborate")
    corroborate.add_argument(
        "case",
        help="Video ID or subject substring of the case to corroborate.",
    )
    corroborate.add_argument("--model", default=LLM_MODEL)
    corroborate.add_argument(
        "--output",
        default="reports/topics/business-failures-corroboration.md",
    )

    review_sample = subparsers.add_parser("review-sample")
    review_sample.add_argument("--per-stratum", type=int, default=2)
    review_sample.add_argument(
        "--stratify-by",
        choices=["case", "mechanism", "epistemic"],
        default="case",
    )
    review_sample.add_argument("--seed", type=int, default=0)
    review_sample.add_argument(
        "--output",
        default="reports/topics/business-failures-label-review.csv",
    )

    review_apply = subparsers.add_parser("review-apply")
    review_apply.add_argument("worksheet")
    review_apply.add_argument(
        "--output",
        default="reports/topics/business-failures-review-overrides.yaml",
    )

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
        scope = _scope_from_args(args)
        hits = query_index(
            args.config,
            args.question,
            limit=args.results,
            scope=scope,
        )
        if not hits:
            print("No passages matched the question within the requested scope.")
        _print_hits(hits)
    elif args.command == "answer":
        scope = _scope_from_args(args)
        result, evidence, invalid = synthesize_answer(
            args.config,
            args.question,
            limit=args.results,
            scope=scope,
            model=args.model,
        )
        markdown = render_answer_md(args.question, result, evidence)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(markdown, encoding="utf-8")
            print(f"Answer ready: {args.output}")
        else:
            print(markdown)
        if invalid:
            print(f"\n[warning] {invalid} claim(s) failed citation validation.")
    elif args.command == "corroborate":
        video_ids = resolve_case_tokens(load_topic_config(args.config), [args.case])
        path, summary = run_corroboration(
            args.config, video_ids[0], args.output, model=args.model
        )
        print(f"Corroboration report ready: {path}")
        print(json.dumps(summary, indent=2))
    elif args.command == "learn":
        path, stats = build_learning_layer(args.config)
        print(f"Learning layer ready: {path}")
        print(json.dumps(stats, indent=2))
    elif args.command == "teach":
        path, stats = build_teaching_layer(args.config, model=args.model)
        print(f"Teaching notes ready: {path}")
        print(json.dumps(stats, indent=2))
    elif args.command == "evaluate-learning":
        path, summary = evaluate_pedagogy(args.config, args.output)
        print(f"Pedagogic evaluation ready: {path}")
        print(json.dumps(summary, indent=2))
    elif args.command == "review-sample":
        path, count = build_review_worksheet(
            args.config,
            args.per_stratum,
            args.stratify_by,
            args.seed,
            args.output,
        )
        print(f"Review worksheet ready: {path} ({count} passages)")
        print(
            "Fill the verdict/add_/remove_/set_epistemic_status/note columns, "
            "then run: topic_corpus.py review-apply " + path
        )
    elif args.command == "review-apply":
        path, summary = apply_review_worksheet(args.worksheet, args.output)
        print(f"Overrides snippet ready: {path}")
        print(json.dumps(summary, indent=2))
        print(
            "Review the snippet, then merge its entries into passage_overrides "
            f"in {args.config} and re-run enrich + index."
        )
    elif args.command == "evaluate":
        _evaluate(args.config, args.questions, args.output)


if __name__ == "__main__":
    main()
