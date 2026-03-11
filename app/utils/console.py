"""Pretty console output for the classifier pipeline.

This module provides user-friendly terminal output with:
- Emojis for visual scanning
- Progress indicators
- Batch details with product samples
- Category breakdowns
- Final summary statistics

Usage:
    from utils.console import console
    console.start("Pipeline Started")
    console.batch_start(1, 10, [0, 1, 2], ["Product A", "Product B"])
    console.batch_result(10, 10, 2.4, {"Cheese": 4, "Meat": 3})
    console.info("Complete!", "All done")

Design principles:
- Isolated from logging (file logs are separate)
- Stateless methods (no side effects beyond printing)
- Easily extensible for new output types
- Configurable via environment variables
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class ConsoleConfig:
    """Configuration for console output behavior."""
    max_category_name_length: int = 40
    box_width: int = 60

    @classmethod
    def from_env(cls) -> "ConsoleConfig":
        """Load configuration from environment variables."""
        return cls(
            max_category_name_length=int(os.getenv("CONSOLE_MAX_CATEGORY_LEN", "40")),
            box_width=int(os.getenv("CONSOLE_BOX_WIDTH", "60")),
        )


class Console:
    """Pretty console output handler for pipeline operations.
    
    Provides methods for different types of output:
    - Phase indicators (start, success, error, warning)
    - Progress tracking (batch progress, overall progress)
    - Data display (products, categories, statistics)
    
    All output goes to stdout and is designed to be human-readable.
    For machine-readable logs, use the logging module instead.
    """

    def __init__(self, config: Optional[ConsoleConfig] = None):
        self.config = config or ConsoleConfig.from_env()
        self._batch_times: List[float] = []

    # ==================== Helpers ====================

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis if too long."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _print(self, *args, **kwargs) -> None:
        """Print to stdout with flush."""
        print(*args, **kwargs, flush=True)

    # ==================== Phase Indicators ====================

    def start(self, message: str, detail: Optional[str] = None) -> None:
        """Display pipeline/phase start message."""
        self._print(f"\n🚀 {message}")
        if detail:
            self._print(f"   └─ {detail}")

    def error(self, message: str, detail: Optional[str] = None) -> None:
        """Display error message."""
        self._print(f"\n❌ {message}")
        if detail:
            self._print(f"   └─ {detail}")

    def info(self, message: str, detail: Optional[str] = None) -> None:
        """Display info message."""
        self._print(f"\n📋 {message}")
        if detail:
            self._print(f"   └─ {detail}")

    # ==================== Data Loading ====================

    def data_loaded(
        self,
        source: str,
        rows: int,
        columns: int,
        elapsed: Optional[float] = None,
    ) -> None:
        """Display data loading result."""
        time_str = f" ({elapsed:.1f}s)" if elapsed is not None else ""
        self._print(f"\n📥 Data Loaded{time_str}")
        self._print(f"   └─ {source}: {rows} rows, {columns} columns")

    # ==================== Classification ====================

    def classification_start(
        self,
        total_rows: int,
        batch_size: int,
        unclassified: int,
    ) -> None:
        """Display classification start info."""
        num_batches = (unclassified + batch_size - 1) // batch_size
        self._print(f"\n🤖 Classification Starting")
        self._print(f"   └─ {unclassified} rows → {num_batches} batches of {batch_size}")
        self._batch_times = []

    def batch_start(
        self,
        batch_num: int,
        total_batches: int,
        row_ids: Sequence[int],
        product_names: Sequence[str],
    ) -> None:
        """Display batch start with product samples."""
        row_range = f"{min(row_ids)}-{max(row_ids)}" if row_ids else "?"
        
        # Simple clean header
        self._print(f"\n┌─ Batch {batch_num}/{total_batches} (Rows {row_range})")
        self._print(f"│  Processing {len(product_names)} products...")
        self._print(f"│")

    def batch_result(
        self,
        classified: int,
        requested: int,
        elapsed: float,
        category_counts: Dict[str, int],
        failed: int = 0,
        tokens: int = 0,
        product_results: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        """Display batch classification results with product→segment mapping."""
        self._batch_times.append(elapsed)
        
        # Show each product with its assigned segment
        if product_results:
            for item in product_results:
                product = self._truncate(item.get("product", ""), 45)
                segment = item.get("segment", "(unclassified)")
                self._print(f"│  • {product:<45} → {segment}")
        
        # Status line
        self._print(f"│")
        tokens_str = f", {tokens:,} tokens" if tokens > 0 else ""
        if failed > 0:
            self._print(f"│  ⚠️  {classified}/{requested} classified in {elapsed:.1f}s{tokens_str} ({failed} failed)")
        else:
            self._print(f"│  ✓ {classified}/{requested} classified in {elapsed:.1f}s{tokens_str}")

        # Box footer
        self._print(f"└{'─' * self.config.box_width}")

    # ==================== Final Summary ====================

    def classification_summary(
        self,
        total_rows: int,
        classified: int,
        unique_categories: int,
        total_categories: int,
        top_categories: List[Dict[str, Any]],
        unexpected: List[str],
        output_path: str,
        elapsed: Optional[float] = None,
    ) -> None:
        """Display final classification summary."""
        coverage_pct = (classified / total_rows * 100) if total_rows > 0 else 0
        
        self._print(f"\n✅ Classification Complete!")
        self._print(f"   ├─ Classified: {classified}/{total_rows} ({coverage_pct:.1f}%)")
        self._print(f"   ├─ Categories used: {unique_categories} of {total_categories}")
        
        # Top categories
        if top_categories:
            self._print(f"   ├─ Top 5:")
            for i, cat in enumerate(top_categories[:5], 1):
                name = self._truncate(cat["category"], self.config.max_category_name_length)
                self._print(f"   │    {i}. {name:<35} {cat['count']:>4} ({cat['pct']:.1f}%)")
        
        # Unexpected categories
        if unexpected:
            self._print(f"   ├─ ⚠️  Unexpected: {len(unexpected)} → {unexpected[:3]}{'...' if len(unexpected) > 3 else ''}")
        
        # Output location
        self._print(f"   └─ Saved: {output_path}")
        
        # Timing
        if elapsed is not None or self._batch_times:
            total_time = elapsed if elapsed is not None else sum(self._batch_times)
            avg_time = sum(self._batch_times) / len(self._batch_times) if self._batch_times else 0
            self._print(f"\n⏱️  Total: {total_time:.1f}s", end="")
            if avg_time > 0:
                self._print(f" (avg {avg_time:.1f}s/batch)")
            else:
                self._print()

    # ==================== Pipeline Status ====================

    def pipeline_finished(self, success: bool = True) -> None:
        """Display pipeline completion status."""
        if success:
            self._print(f"\n{'─' * 50}")
            self._print("🎉 Pipeline finished successfully!")
            self._print(f"{'─' * 50}\n")
        else:
            self._print(f"\n{'─' * 50}")
            self._print("💥 Pipeline failed!")
            self._print(f"{'─' * 50}\n")

    def interrupted(self) -> None:
        """Display interruption message."""
        self._print("\n\n⚡ Interrupted by user")
        self._print("   └─ Partial results may have been saved")


# ==================== Singleton Instance ====================
# This allows: from utils.console import console
console = Console()

__all__ = ["Console", "ConsoleConfig", "console"]
