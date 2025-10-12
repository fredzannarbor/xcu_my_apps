# Requirements Document

## Introduction

This document outlines the requirements for Phase 4 of the LSI Field Enhancement project. The primary goal is to improve the field population rate in LSI CSV outputs, addressing the current issue where a significant percentage of fields remain empty. This phase will focus on enhancing field completion mechanisms, improving default values, and implementing better field mapping strategies.

## Requirements

1.  As a publisher rushing books to market, I need 100% field population with valid fields, including null valids.

2.  As a programmer, I need high transparency: what is happening at each step.

3.  As a systems operator, I need high filterability: show me only warnings, errors, and major decisions.

4.  Specific known issues: 

I only need to view the field report in one format (HTML). No need to create markdown and csv unless requested.
- save llm completions to imprint/metadata/llm_completions BEFORE filtering via field mapping strategies.
- only 2/12 llm completions are showing up in metadata at present. All should be.

5. The top IMMEDiATE priority is that running the pipeline against rows 1-12 of xynapse_traces_schedule.json must create valid fully populated complete LSI csv for those titles.