# BigFive Replacement Imprints

This directory contains 583 imprint configuration templates generated as part of a single batch generation. These imprints are intended to serve as the foundation for a publishing conglomerate with many specialized imprints.

## Status

These are **development templates** - not yet fully configured for production use.

## Purpose

To provide a comprehensive catalog of imprint ideas across diverse genres, topics, and audiences that can be developed into fully operational imprints as needed.

## Usage

Each JSON file contains basic imprint configuration. To activate an imprint:

1. Select an imprint from this directory
2. Move/copy to `imprints/` at project root
3. Create full imprint structure with:
   - `prompts.json` - LLM prompts for content generation
   - `prepress.py` - LaTeX/PDF generation pipeline
   - `template.tex` - Book interior template
   - `cover_template.tex` - Cover design template
   - `schedule.csv` - Book production schedule

See existing imprints (`imprints/nimble_ultra/`, `imprints/xynapse_traces/`) for reference.

## Generation Date

Originally generated as part of the BigFive Replacement publishing initiative.

## File Count

583 imprint configuration files