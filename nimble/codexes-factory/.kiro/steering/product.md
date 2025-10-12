# Codexes Factory: AI-Assisted Publishing Platform

Codexes Factory is a comprehensive publishing platform that leverages AI to streamline the book publishing lifecycle. The platform handles everything from manuscript analysis to distribution-ready file generation.

## Core Features

- **Metadata Generation**: Creates rich metadata for books using LLMs
- **LSI ACS Integration**: Generates CSV files for IngramSpark's Automated Content Submission system
- **Imprint Management**: Supports multiple publishing brands with custom templates and workflows
- **Prepress Pipeline**: Generates interior PDFs and covers using LaTeX templates
- **E-Commerce Integration**: Built-in bookstore with Stripe payment processing
- **Authentication System**: Role-based access control with multiple user types

## Key Concepts

- **Imprints**: Publishing brands with unique branding, templates, and workflows
- **CodexMetadata**: Central metadata object that serves as the single source of truth
- **LSI Fields**: 100+ fields required for Lightning Source Inc. submissions
- **Field Mapping**: System to map metadata to distribution-specific formats
- **LLM Field Completion**: AI-powered generation of subjective metadata fields

## Design Goals

The platform is designed to be extensible, configurable, and maintainable, with hands-off automation and scaling capabilities.