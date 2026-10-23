"""Argument parsing and execution boundaries for the lab commands."""

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from importlib import import_module
from pathlib import Path

from api_support_lab.config import ConfigurationError, load_settings, require_live

CASE_IDS = ("invalid_credentials", "tool_schema", "incomplete_output", "timeout")


def http_status(value: str) -> int:
    try:
        status = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("status must be an integer from 100 to 599") from None
    if not 100 <= status <= 599:
        raise argparse.ArgumentTypeError("status must be an integer from 100 to 599")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="api_support_lab",
        description="API Support Lab: a technical learning lab for API failures and support triage.",
        epilog="Reproduction, triage, and model-backed evaluation require --live.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    reproduce = commands.add_parser("reproduce", help="Reproduce one case attempt (requires --live).")
    reproduce.add_argument("case", choices=CASE_IDS)
    reproduce.add_argument("--variant", choices=("broken", "fixed"), required=True)
    reproduce.add_argument("--live", action="store_true", help="Explicitly permit API requests.")
    reproduce.add_argument("--output-dir", type=Path, help="Evidence directory; defaults to artifacts/evidence in the checkout.")
    reproduce.add_argument("--max-output-tokens", type=int, help="Override the output cap (broken incomplete: 128; otherwise 2048).")
    reproduce.add_argument("--timeout-seconds", type=float, help="Override client timeout (broken timeout: 0.5; otherwise 60).")

    diagnose = commands.add_parser("diagnose", help="Look up diagnostic candidates offline.")
    diagnose.add_argument("--status", type=http_status, required=True)
    diagnose.add_argument("--error-code")

    triage = commands.add_parser("triage", help="Draft a ticket reply (requires --live).")
    triage.add_argument("ticket", type=Path)
    triage.add_argument("--live", action="store_true", help="Explicitly permit API requests.")
    triage.add_argument("--output-dir", type=Path, help="Local run artifact directory.")

    evaluate = commands.add_parser("evaluate", help="Evaluate ten tickets or score saved results offline.")
    evaluate.add_argument("--output-dir", type=Path, help="Local evaluation artifact directory.")
    mode = evaluate.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="Explicitly permit model-backed evaluation.")
    mode.add_argument("--results", type=Path, help="Score saved results offline without model calls.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in ("reproduce", "triage") or (
        args.command == "evaluate" and args.live
    ):
        try:
            require_live(args.live)
        except ConfigurationError as error:
            parser.error(str(error))

    if args.command == "reproduce":
        # Import SDK-dependent case code only after the live boundary.
        case = import_module(f"api_support_lab.cases.{args.case}")

        variant = case.broken if args.variant == "broken" else case.fixed
        options = {"output_dir": args.output_dir} if args.output_dir is not None else {}
        try:
            settings = load_settings()
            if args.max_output_tokens is not None:
                settings = replace(settings, max_output_tokens=args.max_output_tokens)
                if args.case == "incomplete_output" and args.variant == "broken":
                    options["max_output_tokens"] = args.max_output_tokens
            if args.timeout_seconds is not None:
                settings = replace(settings, timeout_seconds=args.timeout_seconds)
                if args.case == "timeout" and args.variant == "broken":
                    options["timeout_seconds"] = args.timeout_seconds
            result = variant(settings, live=args.live, **options)
        except ConfigurationError as error:
            parser.error(str(error))
        except OSError:
            print("Could not write the evidence artifact; the request may already have run.", file=sys.stderr)
            return 1
        print(f"Saved evidence: {result.path}")
        if not case.matches_expected(result):
            print("The attempt did not match the intended behavior; inspect the sanitized evidence.", file=sys.stderr)
            return 1
        print("The attempt matched the intended behavior. Pair verification requires both variants and review.")
        return 0

    if args.command == "diagnose":
        from api_support_lab.runbooks import diagnose

        print(json.dumps(diagnose(args.status, args.error_code)))
        return 0

    if args.command in ("triage", "evaluate"):
        from pydantic import ValidationError
        from yaml import YAMLError

        options = {"output_dir": args.output_dir} if args.output_dir is not None else {}
        try:
            if args.command == "triage":
                from api_support_lab.agent import triage_ticket
                from api_support_lab.tickets import load_ticket

                ticket = load_ticket(args.ticket)
                run = asyncio.run(triage_ticket(ticket, load_settings(), live=args.live, **options))
                print(f"Saved triage run: {run.path}")
                if run.record["status"] != "completed":
                    print("Triage failed; no draft accepted. Inspect the saved run.", file=sys.stderr)
                    return 1
                print("Draft for human review:")
                print(run.record["result"]["customer_reply"])
                return 0
            from api_support_lab.evaluation import evaluate_live, report_passed, score_saved

            if args.results is not None:
                report, path = score_saved(args.results, **options)
            else:
                report, path = asyncio.run(evaluate_live(load_settings(), live=args.live, **options))
            print(f"Saved evaluation report: {path}")
            summary = report["summary"]
            print(f"Automated agreement: {summary['automated_pass']}/{summary['total']}; "
                  f"operational failures: {summary['operational_failures']}; "
                  f"semantic mismatches: {summary['semantic_mismatches']}. Manual reply review required.")
            return 0 if report_passed(report) else 1
        except ConfigurationError as error:
            parser.error(str(error))
        except (ValidationError, YAMLError, ValueError):
            print("Invalid ticket or saved-result data; no usable result produced.", file=sys.stderr)
            return 1
        except OSError:
            print("Could not read or write an artifact; any attempted request was not repeated.", file=sys.stderr)
            return 1

    raise AssertionError("Unhandled command")
