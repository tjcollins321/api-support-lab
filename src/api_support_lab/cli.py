"""Argument parsing and execution boundaries for the planned lab commands."""

import argparse
import sys
from collections.abc import Sequence
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
        epilog="Authentication reproduction requires --live; other command handlers remain planned.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    reproduce = commands.add_parser("reproduce", help="Reproduce a case (authentication implemented; requires --live).")
    reproduce.add_argument("case", choices=CASE_IDS)
    reproduce.add_argument("--variant", choices=("broken", "fixed"), required=True)
    reproduce.add_argument("--live", action="store_true", help="Explicitly permit API requests.")
    reproduce.add_argument("--output-dir", type=Path, help="Evidence directory; defaults to artifacts/evidence in the checkout.")

    diagnose = commands.add_parser("diagnose", help="Look up diagnostic candidates offline (planned).")
    diagnose.add_argument("--status", type=http_status, required=True)
    diagnose.add_argument("--error-code")

    triage = commands.add_parser("triage", help="Draft a ticket reply (planned; requires --live).")
    triage.add_argument("ticket", type=Path)
    triage.add_argument("--live", action="store_true", help="Explicitly permit API requests.")

    evaluate = commands.add_parser("evaluate", help="Evaluate tickets or score saved results (planned).")
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

    if args.command == "reproduce" and args.case == "invalid_credentials":
        # Import SDK-dependent case code only after the live boundary.
        from api_support_lab.cases import invalid_credentials

        variant = invalid_credentials.broken if args.variant == "broken" else invalid_credentials.fixed
        options = {"output_dir": args.output_dir} if args.output_dir is not None else {}
        try:
            result = variant(load_settings(), live=args.live, **options)
        except ConfigurationError as error:
            parser.error(str(error))
        except OSError:
            print("Could not write the evidence artifact; the request may already have run.", file=sys.stderr)
            return 1
        print(f"Saved evidence: {result.path}")
        if not invalid_credentials.matches_expected(result):
            print("The attempt did not match the intended behavior; inspect the sanitized evidence.", file=sys.stderr)
            return 1
        print("The attempt matched the intended behavior. Pair verification requires both variants and review.")
        return 0

    # Do not load credentials or construct clients for unimplemented handlers.
    print(f"{args.command} is not implemented yet; no operation was performed.", file=sys.stderr)
    return 1
