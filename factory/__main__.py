"""Command line: python -m factory run <ticket.json> | status <run_dir> | summary <run_dir>..."""

from __future__ import annotations

import argparse
import sys

from factory import driver, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m factory", description="Run a ticket through the QA factory."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="run or resume a ticket")
    run_p.add_argument("ticket", help="path to the ticket JSON")
    run_p.add_argument("--runs-root", default=".artifacts/runs", help="folder holding run folders")
    run_p.add_argument("--until", default=None, help="stop after this step (e.g. implement)")
    status_p = sub.add_parser("status", help="show the step records of a run")
    status_p.add_argument("run_dir", help="path to a run folder")
    summary_p = sub.add_parser("summary", help="print the comparison numbers of one or more runs")
    summary_p.add_argument("run_dirs", nargs="+", help="paths to run folders")
    summary_p.add_argument("--json", default=None, help="write the numbers here as JSON")
    args = parser.parse_args(argv)
    if args.command == "run":
        return driver.run(args.ticket, runs_root=args.runs_root, until=args.until)
    if args.command == "summary":
        return summary.main(args.run_dirs, args.json)
    return driver.status(args.run_dir)


if __name__ == "__main__":
    sys.exit(main())
