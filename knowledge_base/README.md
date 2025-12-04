# Knowledge Base for RAG (Retrieval-Augmented Generation)

This directory contains best practice documents used by the RAG service to enhance resume tailoring with market-specific guidance.

## Structure

Documents are organized by:
- **Market**: Russian, US, UK
- **Industry**: Tech, Finance, General
- **Role**: Backend, Fullstack, GPT Engineer
- **Category**: Guidelines, ATS optimization, Formatting, Examples

## Current Documents

### Market-Specific Guidelines
- `russian_general_guidelines.md` - Russian resume conventions and best practices
- `english_us_guidelines.md` - US market resume conventions and best practices

### Industry-Specific
- `tech_backend_best_practices.md` - Backend developer resume best practices

### General
- `ats_optimization.md` - ATS (Applicant Tracking System) optimization strategies

## Adding New Documents

1. Create a new `.md` file in this directory
2. Use descriptive filename that includes:
   - Market (russian, english, us, uk)
   - Industry (tech, finance, etc.)
   - Role (backend, fullstack, gpt_engineer)
   - Category (guidelines, ats, formatting, examples)

3. The RAG service will automatically:
   - Load the document on startup
   - Extract metadata from filename
   - Index it for retrieval

## Document Format

Each document should:
- Be written in Markdown
- Include clear sections and headers
- Provide actionable advice
- Include examples when relevant
- Be specific to the target market/industry

## Metadata Extraction

The RAG service automatically extracts metadata from filenames:
- **Language**: Detected from "russian" or "english"/"us"/"uk" in filename
- **Market**: Detected from market-specific keywords
- **Industry**: Detected from industry keywords (tech, finance, etc.)
- **Role**: Detected from role keywords (backend, fullstack, gpt_engineer)
- **Category**: Detected from category keywords (guidelines, ats, formatting)

## Usage

Documents are automatically used when:
- Generating tailored resumes
- Language matches document language
- Role matches document role
- Job description is semantically similar

The RAG service retrieves the most relevant documents and includes them in the LLM prompt for enhanced tailoring.

