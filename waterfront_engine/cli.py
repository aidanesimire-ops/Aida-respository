"""Command line entry point.

    python -m waterfront_engine.cli verify-fields --market configs/fort_lauderdale.py
    python -m waterfront_engine.cli run          --market configs/fort_lauderdale.py
    python -m waterfront_engine.cli demo         --out-dir demo_output
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .pipeline import STAGES

DEFAULT_MARKET = "configs/fort_lauderdale.py"


def _log_setup(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname).1s %(asctime)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="waterfront-engine", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--market", default=DEFAULT_MARKET, help="path to a market config file")
        p.add_argument("--data-dir", default="data", help="working directory for stage files")
        p.add_argument("--out-dir", default=".", help="where the workbooks are written")

    verify = sub.add_parser("verify-fields", help="check the field map against the live layer")
    common(verify)
    verify.add_argument("--json", dest="json_out", help="write the full report to this path")

    run = sub.add_parser("run", help="run the pipeline")
    common(run)
    run.add_argument(
        "--stages",
        default="all",
        help=f"comma-separated subset of: {','.join(STAGES)} (default: all)",
    )
    run.add_argument("--no-sunbiz", action="store_true", help="skip entity enrichment")
    run.add_argument(
        "--bulk-entities",
        help="CSV/parquet of pre-parsed state entity filings to match instead of live lookups",
    )
    run.add_argument("--sunbiz-delay", type=float, default=1.6, help="seconds between lookups")

    demo = sub.add_parser("demo", help="run end to end on a synthetic fixture (no network)")
    demo.add_argument("--market", default=DEFAULT_MARKET)
    demo.add_argument("--out-dir", default="demo_output")

    return parser


def _resolver(args: argparse.Namespace, data_dir: Path):
    if args.no_sunbiz:
        return None
    if args.bulk_entities:
        from .sunbiz import BulkEntityIndex

        return BulkEntityIndex(args.bulk_entities)
    from .sunbiz import SunbizClient

    return SunbizClient(data_dir / "sunbiz_cache.json", delay=args.sunbiz_delay)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _log_setup(getattr(args, "verbose", False))
    log = logging.getLogger("waterfront_engine")

    if args.command == "demo":
        from .demo import run_demo

        paths = run_demo(Path(args.out_dir), market_path=args.market)
        for label, path in paths.items():
            print(f"{label}: {path}")
        return 0

    try:
        cfg = load_config(args.market, data_dir=args.data_dir, out_dir=args.out_dir)
    except ConfigError as exc:
        log.error("%s", exc)
        return 2

    if args.command == "verify-fields":
        from .arcgis import ArcGISError
        from .pipeline import verify_fields

        try:
            report = verify_fields(cfg)
        except ArcGISError as exc:
            log.error("could not reach the parcel layer: %s", exc)
            return 3

        print(f"layer: {report['layer']}")
        print(f"fields on layer: {report['field_count']}   features: {report.get('feature_count', '?')}")
        print(f"mapped OK: {len(report['mapped_ok'])}")
        missing = report["missing"]
        if missing:
            print("\nUNMAPPED — fix these in MARKET before running:")
            for key, hints in missing.items():
                shown = ", ".join(hints) if hints else "(no obvious candidate)"
                print(f"  {key:<12} configured {cfg.market.fields.get(key)!r}; candidates: {shown}")
        else:
            print("\nevery configured field exists on the layer.")
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(report, indent=2, default=str))
            print(f"\nfull report: {args.json_out}")
        return 1 if missing else 0

    # -- run ------------------------------------------------------------
    from . import pipeline

    stages = STAGES if args.stages == "all" else tuple(s.strip() for s in args.stages.split(","))
    unknown = [s for s in stages if s not in STAGES]
    if unknown:
        log.error("unknown stage(s): %s (valid: %s)", unknown, ", ".join(STAGES))
        return 2

    if "fetch" in stages:
        pipeline.fetch(cfg)
    if "classify" in stages:
        pipeline.classify_stage(cfg)
    if "waterfront" in stages:
        pipeline.waterfront_stage(cfg)
    if "flags" in stages:
        pipeline.flags_stage(cfg)
    if "enrich" in stages:
        resolver = _resolver(args, Path(args.data_dir))
        if resolver is None:
            log.info("skipping entity enrichment (--no-sunbiz)")
        else:
            pipeline.enrich_stage(cfg, resolver)
    if "workbooks" in stages:
        ownership = pipeline.build_ownership_workbook(cfg)
        condo = pipeline.build_condo_workbook(cfg)
        report = pipeline.write_run_report(cfg)
        print(f"ownership workbook: {ownership}")
        if condo:
            print(f"condo workbook:     {condo}")
        print(f"run report:         {report}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
