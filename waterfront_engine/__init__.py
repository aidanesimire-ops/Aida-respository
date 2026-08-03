"""Waterfront Property List Engine — off-market ownership call sheets.

Public ownership records (county property appraiser + state business filings)
joined to county hydrography, split by asset class, flagged for entity and
absentee ownership, and written to two styled workbooks. No MLS or listing data
is used anywhere, so no owner is included or excluded by listing status.

    from waterfront_engine import load_config, pipeline

    cfg = load_config("configs/fort_lauderdale.py")
    pipeline.fetch(cfg)
    pipeline.classify_stage(cfg)
    pipeline.waterfront_stage(cfg)
    pipeline.flags_stage(cfg)
    pipeline.build_ownership_workbook(cfg)
"""

from .config import AssetClass, CondoDeliverable, ConfigError, Market, MarketConfig, load_config

__all__ = [
    "AssetClass",
    "CondoDeliverable",
    "ConfigError",
    "Market",
    "MarketConfig",
    "load_config",
]
__version__ = "1.0.0"
