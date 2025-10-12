# Interior Prepress & Book Format Assessment & Fix Plan

## Current Status Assessment
- [x] Korean font handling improvements implemented
- [ ] Test LaTeX compilation with various content types
- [ ] Validate bibliography formatting
- [ ] Check table of contents generation
- [ ] Test watermark and page numbering

## Issues to Fix
1. **Font Handling**: Ensure Korean text processor works consistently
2. **LaTeX Escaping**: Fix PROTECTED_LATEX placeholder issues
3. **Bibliography**: Implement proper hanging indent formatting
4. **TOC Generation**: Ensure two-pass compilation works
5. **Template Consistency**: Standardize across imprints

## Testing Strategy
```bash
# Test prepress pipeline
python run_book_pipeline.py --imprint xynapse_traces --schedule-file configs/tranches/xynapse_tranche_1.json --model gemini/gemini-2.5-flash --start-stage 3 --end-stage 3
```

## Success Criteria
- [ ] Korean text renders correctly throughout document
- [ ] Bibliography has proper hanging indents
- [ ] Table of contents is populated
- [ ] No LaTeX compilation errors
- [ ] Consistent formatting across all sections