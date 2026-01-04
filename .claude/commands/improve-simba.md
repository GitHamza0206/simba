# improve-simba

Analyze RAG evaluation results and implement targeted improvements to the Simba customer service assistant.

## What this skill does

This skill receives evaluation results from Simba's evaluation system in JSON format and systematically improves the RAG pipeline based on identified issues. It analyzes retrieval quality, model responses, and user feedback to implement targeted fixes.

## Usage

```bash
claude improve-simba '{
  "evaluation_results": [
    {
      "id": "eval_001",
      "question": "What is your return policy?",
      "response": "I apologize, but I could not find information about our return policy.",
      "sources": ["shipping-guide.pdf (score: 0.72)", "faq.pdf (score: 0.68)"],
      "sources_groundtruth": ["return-policy.pdf", "electronics-warranty.pdf"],
      "comment": "Wrong documents retrieved - got shipping info instead of return policy",
      "latency_ms": 850
    }
  ],
  "aggregate_metrics": {
    "recall_at_k": 0.45,
    "precision_at_k": 0.32,
    "mrr": 0.28
  }
}'
```

## Instructions

You are an expert at improving Retrieval-Augmented Generation (RAG) systems. Your task is to analyze the provided evaluation results from Simba (a customer service assistant) and implement systematic improvements.

### Input Format Expected

The evaluation data in `$ARGUMENTS` should contain:

```typescript
interface EvalItem {
  id: string;
  question: string;                    // The evaluation question
  response: string | null;             // Generated response
  sources: string[] | null;            // Retrieved sources (format: "doc.pdf (score: 0.85)")
  sources_groundtruth: string[] | null; // Expected/correct sources
  comment: string | null;              // Human annotation/feedback - CRITICAL
  latency_ms: number | null;           // Response latency
}

interface EvaluationData {
  evaluation_results: EvalItem[];
  aggregate_metrics?: {
    recall_at_k: number;
    precision_at_k: number;
    mrr: number;
  };
}
```

### Step 1: Parse and Analyze Evaluation Data

1. **Extract evaluation results** from `$ARGUMENTS`
2. **Identify problem patterns**:
   - **Retrieval Issues**: Expected sources missing, wrong sources retrieved
   - **Response Quality**: Poor or incorrect responses despite good sources
   - **Latency Issues**: Slow response times
   - **User Comments**: Most valuable signal for specific problems

3. **Calculate metrics**:
   - Recall: How many expected sources were actually retrieved
   - Precision: How many retrieved sources were relevant
   - Common failure patterns across queries

### Step 2: Examine Current Configuration

Before making changes, examine the current RAG pipeline:

1. **Read current configuration** in `/Users/mac/projects/simba/simba/core/config.py`
2. **Review chunking strategy** in `/Users/mac/projects/simba/simba/services/chunker_service.py`
3. **Check prompt template** in `/Users/mac/projects/simba/simba/services/chat_service.py`
4. **Understand retrieval logic** in `/Users/mac/projects/simba/simba/services/retrieval_service.py`

### Step 3: Implement Targeted Improvements

Based on your analysis, make specific improvements:

#### For Retrieval Issues

- **Lower similarity threshold** if good sources are being filtered out
- **Increase retrieval limit** if not getting enough candidate sources
- **Enable/tune hybrid search** for keyword-heavy queries
- **Adjust reranking settings** if ranking is poor

#### For Chunking Issues

- **Modify chunk size**: Smaller for precise facts (500-800), larger for context (1200-1500)
- **Adjust overlap**: More overlap for better context continuity
- **Update separators**: Better for document structure

#### For Prompt Issues

- **Improve system prompt** to better guide response generation
- **Add instructions** for handling missing information
- **Enhance context usage guidelines**

### Step 4: Make Actual Code Changes

When you identify specific improvements needed, implement them:

**Example config changes in `/Users/mac/projects/simba/simba/core/config.py`:**

```python
# Lower threshold for better recall
retrieval_min_score: float = 0.6  # was 0.7

# Increase candidates for reranking
retrieval_limit: int = 8  # was 5
```

**Example chunking changes in `/Users/mac/projects/simba/simba/services/chunker_service.py`:**

```python
def chunk_text(
    text: str,
    chunk_size: int = 800,  # adjusted from 1000
    chunk_overlap: int = 150,  # adjusted from 200
):
```

**Example prompt improvements in `/Users/mac/projects/simba/simba/services/chat_service.py`:**

```python
SYSTEM_PROMPT = """You are Simba, a helpful customer service assistant.

Your role is to help users by:
1. Answering questions using information from the knowledge base (RAG)
2. Being friendly, professional, and concise
3. Admitting when you don't know something but offering alternatives

When using the rag tool:
- Search with the most relevant keywords from the user's question
- Pay attention to the retrieved sources and their relevance scores
- Base your answers on the retrieved context when available
- If sources are partially relevant, extract what you can and acknowledge limitations

If you cannot find relevant information, suggest alternative ways to help."""
```

### Step 5: Provide Implementation Summary

After making changes, provide a comprehensive summary:

```markdown
## Evaluation Analysis Summary

### Issues Identified
- Total evaluation items: X
- Items with retrieval failures: X
- Items with response issues: X
- Items with user feedback: X

### Critical Problems (from user comments)
1. [Issue description based on comments]
   - Root cause: [retrieval/chunking/prompt/content]
   - Items affected: [eval IDs]

### Retrieval Performance Analysis
- Recall@k: X% (expected sources found)
- Precision@k: X% (retrieved sources relevant)
- Common missing sources: [patterns identified]

### Implemented Changes

#### Configuration Updates
- File: `/Users/mac/projects/simba/simba/core/config.py`
- Changes: [list specific parameter changes with reasoning]

#### Code Improvements
- File: [path]
- Changes: [description of modifications]

#### Reasoning for Changes
[Explain why each change addresses the identified issues]

### Expected Impact
- Improved recall for [specific query types]
- Better response quality for [specific scenarios]
- Reduced latency for [if applicable]

### Validation Steps
1. Re-run evaluations with same queries
2. Monitor metrics improvement
3. Test edge cases mentioned in feedback
```

### Key Files to Examine/Modify

- `/Users/mac/projects/simba/simba/core/config.py` - RAG parameters and thresholds
- `/Users/mac/projects/simba/simba/services/retrieval_service.py` - Core retrieval logic
- `/Users/mac/projects/simba/simba/services/chunker_service.py` - Text chunking strategy
- `/Users/mac/projects/simba/simba/services/chat_service.py` - System prompt and response generation
- `/Users/mac/projects/simba/simba/services/reranker_service.py` - Cross-encoder reranking

### Important Guidelines

1. **Make incremental changes** - don't modify everything at once
2. **Focus on user comments** - they provide the most specific guidance
3. **Consider trade-offs** - improving recall might reduce precision
4. **Test thoroughly** - re-run evaluations to validate improvements
5. **Document reasoning** - explain why each change was made

The goal is to systematically improve the RAG pipeline based on concrete evaluation evidence and user feedback.

---

$ARGUMENTS
