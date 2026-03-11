from __future__ import annotations

import json
from typing import Dict, List

import pandas as pd


class PromptBuilder:
    """Build classification prompts from config-driven parameters."""

    def __init__(
        self,
        context_columns: List[str],
        instructions_template: str,
        response_key: str,
        fallback_label: str,
    ):
        self.context_columns = list(context_columns)
        self.instructions_template = instructions_template
        self.response_key = response_key
        self.fallback_label = fallback_label

    def build_classification_prompt(
        self,
        batch_df,
        context: str,
        label_names: List[str],
        label_descriptions: Dict[str, str],
    ) -> str:
        """Build prompt for classification."""
        if "ROW_ID" not in batch_df.columns:
            raise ValueError("batch_df must contain a 'ROW_ID' column")
        
        present_cols = [c for c in self.context_columns if c in batch_df.columns]
        minimal_df = batch_df[["ROW_ID"] + present_cols].copy()
        
        # Build product rows
        rows = []
        for _, row in minimal_df.iterrows():
            row_obj = {"row_id": int(row["ROW_ID"])}
            for c in present_cols:
                val = row[c]
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    val = ""
                row_obj[c] = str(val)
            rows.append(json.dumps(row_obj, ensure_ascii=False))
        rows_text = "\n".join(rows)
        
        # Build label descriptions
        label_text = []
        for label in label_names:
            description = label_descriptions.get(label, "")
            if description:
                label_text.append(f"- {label}: {description}")
            else:
                label_text.append(f"- {label}")
        labels_str = "\n".join(label_text)
        
        columns_text = ", ".join(present_cols) if present_cols else "(no context)"
        instructions = self.instructions_template.format(
            columns=columns_text,
            fallback_label=self.fallback_label,
            response_key=self.response_key,
        )
        
        context_part = f"Additional context: {context.strip()}" if context else "Additional context: (none)"
        
        sample_label = label_names[0] if label_names else "Example"
        prompt = (
            f"{instructions}\n\n{context_part}\n\n"
            f"Available Labels:\n{labels_str}\n\n"
            f"Products to classify:\n{rows_text}\n\n"
            f'Return JSON array ONLY, e.g.: [{{"row_id": 12, "{self.response_key}": "{sample_label}"}}]'
        )
        return prompt


__all__ = ["PromptBuilder"]
