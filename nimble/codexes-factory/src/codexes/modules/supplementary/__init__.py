"""
Supplementary materials module.

Handles loading and processing of supplementary materials (txt, markdown, docx, pdf)
for inclusion in LLM prompts with imprint configurations.
"""

from .materials_loader import (
    SupplementaryMaterialsLoader,
    load_imprint_supplementary_materials,
    get_largest_context_model
)

__all__ = [
    "SupplementaryMaterialsLoader",
    "load_imprint_supplementary_materials",
    "get_largest_context_model"
]
