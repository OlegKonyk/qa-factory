"""Command line: python -m factory run <ticket.json> | status | summary | report | roadmap | restate ..."""

from __future__ import annotations

import argparse
import json
import sys

from factory import driver, report, roadmap, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m factory", description="Run a ticket through the QA factory."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="run or resume a ticket")
    run_p.add_argument("ticket", help="path to the ticket JSON")
    run_p.add_argument("--runs-root", default=".artifacts/runs", help="folder holding run folders")
    run_p.add_argument("--until", default=None, help="stop after this step (e.g. implement)")
    run_p.add_argument(
        "--engine",
        choices=["driver", "restate"],
        default="driver",
        help="driver (default) runs here and now; restate starts the ticket's workflow on a Restate server",
    )
    run_p.add_argument("--key", default=None, help="restate: the workflow key (default: the ticket id)")
    status_p = sub.add_parser("status", help="show the step records of a run")
    status_p.add_argument("run_dir", help="path to a run folder")
    summary_p = sub.add_parser("summary", help="print the comparison numbers of one or more runs")
    summary_p.add_argument("run_dirs", nargs="+", help="paths to run folders")
    summary_p.add_argument("--json", default=None, help="write the numbers here as JSON")
    report_p = sub.add_parser("report", help="write the Markdown QA evidence page of one run")
    report_p.add_argument("run_dir", help="path to a run folder")
    report_p.add_argument("--out", default=None, help="write the page here (default <run_dir>/report.md)")
    dev_p = sub.add_parser("devtests", help="the revert check on the developers' own tests of a finished run")
    dev_p.add_argument("run_dir", help="path to a run folder")
    roadmap_p = sub.add_parser("roadmap", help="show the state of each item in docs/roadmap.md")
    roadmap_p.add_argument("--path", default=None, help="the roadmap file (default docs/roadmap.md)")
    roadmap_p.add_argument("--json", action="store_true", help="print JSON instead of a table")
    restate_p = sub.add_parser("restate", help="the factory as a Restate workflow")
    restate_sub = restate_p.add_subparsers(dest="action", required=True)
    serve_p = restate_sub.add_parser("serve", help="serve the workflow for the Restate server")
    serve_p.add_argument("--port", type=int, default=9080)
    serve_p.add_argument("--steps", default=None, help="module whose STEPS replace the real steps")
    register_p = restate_sub.add_parser("register", help="register the served workflow with Restate")
    register_p.add_argument("--uri", default="http://127.0.0.1:9080")
    answer_p = restate_sub.add_parser("answer", help="resolve the gate a run waits on")
    answer_p.add_argument("key", help="the workflow key (the ticket id unless --key was given)")
    answer_p.add_argument("answer", help="path to the answer JSON")
    args = parser.parse_args(argv)
    if args.command == "restate" or getattr(args, "engine", None) == "restate":
        from factory import restate_service  # needs the Restate SDK, a dev dependency
    if args.command == "run" and args.engine == "restate":
        if args.until:
            parser.error("--until works with the plain driver only")
        print(json.dumps(restate_service.submit(args.ticket, args.key, args.runs_root)))
        return 0
    if args.command == "run":
        return driver.run(args.ticket, runs_root=args.runs_root, until=args.until)
    if args.command == "restate":
        if args.action == "serve":
            return restate_service.serve(args.port, args.steps)
        result = (
            restate_service.register(args.uri)
            if args.action == "register"
            else restate_service.answer(args.key, args.answer)
        )
        print(json.dumps(result))
        return 0
    if args.command == "summary":
        return summary.main(args.run_dirs, args.json)
    if args.command == "roadmap":
        return roadmap.main(args.path, args.json)
    if args.command == "devtests":
        from factory.checks import devtests

        return devtests.main(args.run_dir)
    if args.command == "report":
        return report.main(args.run_dir, args.out)
    return driver.status(args.run_dir)


if __name__ == "__main__":
    sys.exit(main())
