# RAG Implementation Plan for Resume Tailoring

## Overview

This document outlines the implementation of Retrieval-Augmented Generation (RAG) to enhance resume tailoring with market-specific best practices, styling guidelines, and ATS optimization strategies.

## Goals

1. **Market-Specific Guidance**: Provide Russian and English (US/UK) market-specific resume formatting and style recommendations
2. **Best Practices Integration**: Leverage successful resume examples and industry standards
3. **ATS Optimization**: Improve keyword matching and formatting for Applicant Tracking Systems
4. **Quality Enhancement**: Increase resume quality by 20-30% through context-aware suggestions

## Architecture

### Components

```
┌─────────────────┐
│  Resume Text    │
│  Job Description │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RAG Retriever   │───► Query Vector DB
│  (by language,   │     (FAISS/Chroma)
│   role, market)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Best Practices  │
│  Context         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Enhanced LLM    │
│  Prompt          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tailored Resume │
└─────────────────┘
```

## Phase 1: Knowledge Base Setup

### 1.1 Document Curation

Create knowledge base documents in `knowledge_base/`:

**Russian Market:**
- `russian_general_guidelines.md` - General Russian resume conventions
- `russian_tech_industry.md` - Tech industry specifics
- `russian_ats_optimization.md` - ATS tips for Russian market
- `russian_formatting_examples.md` - Formatting examples

**English Markets:**
- `english_us_guidelines.md` - US market conventions
- `english_uk_guidelines.md` - UK market conventions
- `english_ats_optimization.md` - ATS optimization (US/UK)
- `english_formatting_examples.md` - Formatting examples

**Industry-Specific:**
- `tech_backend_best_practices.md` - Backend developer best practices
- `tech_fullstack_best_practices.md` - Fullstack developer best practices
- `tech_gpt_engineer_best_practices.md` - GPT/AI engineer best practices

**General:**
- `ats_keyword_strategies.md` - Keyword optimization strategies
- `action_verbs_guide.md` - Strong action verbs by language
- `metrics_and_achievements.md` - How to quantify achievements

### 1.2 Document Structure

Each document should include:
- Market/industry context
- Formatting guidelines
- Section ordering recommendations
- Style tips (tone, length, structure)
- Common mistakes to avoid
- Examples (anonymized)

## Phase 2: Vector Database Setup

### 2.1 Technology Choice

**Option 1: FAISS (Recommended for MVP)**
- Pros: Fast, local, no external dependencies
- Cons: In-memory, needs persistence layer
- Use case: MVP and development

**Option 2: Chroma**
- Pros: Persistent, easy API, good for production
- Cons: Additional dependency
- Use case: Production deployment

**Decision**: Start with FAISS for MVP, can migrate to Chroma later.

### 2.2 Embedding Model

- Use OpenAI `text-embedding-3-small` (cost-effective, good quality)
- Alternative: `text-embedding-ada-002` (older, cheaper)
- Store embeddings locally for faster retrieval

### 2.3 Index Structure

Index documents with metadata:
- `language`: "ru" | "en"
- `market`: "ru" | "us" | "uk" | "general"
- `industry`: "tech" | "finance" | "general"
- `role`: "backend" | "fullstack" | "gpt_engineer" | "general"
- `category`: "formatting" | "ats" | "style" | "examples"

## Phase 3: RAG Service Implementation

### 3.1 Retrieval Logic

```python
def retrieve_best_practices(
    language: LanguageCode,
    target_role: TargetRole,
    job_description: str,
    top_k: int = 3
) -> list[str]:
    """
    Retrieve relevant best practices based on:
    - Target language and market
    - Target role/industry
    - Job description keywords
    """
```

**Retrieval Strategy:**
1. Query by metadata (language, role) - exact match
2. Semantic search on job description - similarity match
3. Combine and rank results
4. Return top K most relevant documents

### 3.2 Integration Points

**Current Flow:**
```
generate_tailored_resume_llm() 
  → system_prompt + user_prompt 
  → OpenAI API
```

**Enhanced Flow:**
```
generate_tailored_resume_llm()
  → retrieve_best_practices() 
  → enhanced_system_prompt (with RAG context)
  → enhanced_user_prompt
  → OpenAI API
```

## Phase 4: Enhanced Prompts

### 4.1 System Prompt Enhancement

**Before:**
```
"You are an assistant that rewrites CVs truthfully..."
```

**After:**
```
"You are an assistant that rewrites CVs truthfully...

MARKET-SPECIFIC GUIDELINES:
{retrieved_best_practices}

Follow these guidelines when tailoring the resume..."
```

### 4.2 User Prompt Enhancement

Add retrieved context as reference material:
```
"REFERENCE MATERIAL (for guidance only):
{retrieved_examples}

TASK: Rewrite the resume following the guidelines above..."
```

## Phase 5: Configuration

### 5.1 Environment Variables

```bash
# RAG Configuration
RAG_ENABLED=true
RAG_TOP_K=3  # Number of documents to retrieve
RAG_SIMILARITY_THRESHOLD=0.7  # Minimum similarity score
EMBEDDING_MODEL=text-embedding-3-small
```

### 5.2 Feature Flags

- Make RAG optional (can disable for faster/stub responses)
- Allow users to choose style presets
- A/B testing capability

## Phase 6: Testing Strategy

### 6.1 Unit Tests
- Vector DB indexing
- Retrieval logic
- Embedding generation
- Metadata filtering

### 6.2 Integration Tests
- End-to-end RAG flow
- Prompt enhancement
- Quality comparison (with/without RAG)

### 6.3 Quality Metrics
- Resume quality score (subjective evaluation)
- ATS keyword coverage improvement
- Market-appropriateness rating

## Implementation Steps

### Step 1: Setup (Current)
- [x] Create implementation plan
- [ ] Set up vector database infrastructure
- [ ] Create knowledge base directory structure

### Step 2: Knowledge Base
- [ ] Write Russian market guidelines
- [ ] Write English market guidelines
- [ ] Write industry-specific best practices
- [ ] Create examples and templates

### Step 3: RAG Service
- [ ] Implement embedding generation
- [ ] Implement vector database indexing
- [ ] Implement retrieval logic
- [ ] Add caching for performance

### Step 4: Integration
- [ ] Integrate RAG into `generate_tailored_resume_llm()`
- [ ] Update prompts with RAG context
- [ ] Add configuration options
- [ ] Make it optional/experimental

### Step 5: Testing & Documentation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update API documentation
- [ ] Create user guide

## Dependencies

### New Python Packages
```txt
faiss-cpu==1.7.4  # Vector database (or faiss-gpu for GPU)
# OR
chromadb==0.4.22  # Alternative vector database
```

### Existing (Already Installed)
- `openai` - For embeddings and LLM
- `numpy` - For vector operations (dependency of FAISS)

## Performance Considerations

1. **Embedding Caching**: Cache embeddings for knowledge base documents
2. **Index Persistence**: Save FAISS index to disk, reload on startup
3. **Async Retrieval**: Make RAG retrieval async to not block requests
4. **Batch Processing**: Process multiple retrievals in parallel

## Future Enhancements

1. **User Feedback Loop**: Learn from successful applications
2. **Dynamic Knowledge Base**: Update based on market trends
3. **Multi-language Support**: Expand beyond Russian/English
4. **Industry Expansion**: Add more industries (finance, consulting, etc.)
5. **Style Presets**: Pre-configured style combinations
6. **ATS Score Prediction**: Predict ATS compatibility score

## Success Metrics

- **Quality Improvement**: 20-30% better market alignment
- **ATS Compatibility**: 15-25% better keyword matching
- **User Satisfaction**: Higher ratings for tailored resumes
- **Processing Time**: <2s additional latency (acceptable trade-off)

## Timeline Estimate

- **Phase 1-2** (Knowledge Base + Setup): 2-3 days
- **Phase 3** (RAG Service): 2-3 days
- **Phase 4** (Integration): 1-2 days
- **Phase 5** (Testing): 1-2 days
- **Total**: ~1-2 weeks for MVP

## Risk Mitigation

1. **Knowledge Base Quality**: Start with curated, high-quality documents
2. **Performance**: Use caching and async operations
3. **Cost**: Embedding costs are minimal, reuse cached embeddings
4. **Complexity**: Keep RAG optional, fallback to current system if disabled

