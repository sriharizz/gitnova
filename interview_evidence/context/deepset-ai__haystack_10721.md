# Issue Context Dossier: `deepset-ai/haystack` #10721

**Title:** Connecting multiple `documents` outputs to `PromptBuilder.documents` is not possible  
**Repository:** https://github.com/deepset-ai/haystack  
**Language:** Python  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Connecting multiple retriever outputs (such as retriever_1 and retriever_2) to a single PromptBuilder input socket like prompt_builder.documents fails with a PipelineConnectError because PromptBuilder handles input variables dynamically based on its template, often typing them as Any instead of using a variadic annotation like Variadic[List[Document]], preventing the pipeline connection logic from recognizing it as capable of accepting multiple incoming connections.

## 2. Root Cause Analysis
> In Haystack pipelines, receiving input sockets only accept multiple incoming connections if they are designated as variadic (either lazy or greedy variadic via `Variadic[...]` type annotations). When `PromptBuilder` parses templates or initializes inputs, sockets corresponding to template variables default to `Any` if not explicitly constrained or typed. As a result, `InputSocket.is_lazy_variadic` and `InputSocket.is_greedy` evaluate to False, and pipeline connection checks reject any subsequent connections after the first one.

## 3. Grounded Code Locations & Citations
- File: `haystack/core/component/types.py` (Lines: `39-111`) | Symbol: `InputSocket` | Role: *Defines input socket properties including variadic detection and type un-wrapping logic.* (Verified: True)
- File: `haystack/core/pipeline/base.py` (Lines: `1842-1859`) | Symbol: `_write_to_lazy_variadic_socket` | Role: *Handles writing and aggregating incoming values for lazy variadic sockets.* (Verified: True)
- File: `haystack/core/pipeline/component_checks.py` (Lines: `177-190`) | Symbol: `has_lazy_variadic_socket_received_all_inputs` | Role: *Validates whether a lazy variadic socket has received inputs from all expected senders.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect PromptBuilder input initialization**: Inspect how PromptBuilder initializes its input sockets and templates in haystack/components/builders/prompt_builder.py to identify where template variables are typed as Any. (Target: `haystack/components/builders/prompt_builder.py`)
2. **Update template variable typing to support Variadic lists**: Modify the input socket type definition for template variables in PromptBuilder to allow Variadic[List[Document]] or similar variadic annotations when the input is intended to accept multiple connections. (Target: `haystack/components/builders/prompt_builder.py`)
3. **Verify socket variadic checks in pipeline connection logic**: Inspect haystack/core/pipeline/base.py and haystack/core/component/types.py to ensure that InputSocket correctly identifies the updated PromptBuilder sockets as variadic. (Target: `haystack/core/pipeline/base.py`)
4. **Write regression test for multiple retriever connections**: Add a regression test in tests/core/pipeline/test_pipeline.py or a component builder test file connecting multiple retriever outputs to prompt_builder.documents and asserting successful execution and aggregation. (Target: `tests/core/pipeline/test_pipeline.py`)
5. **Run test suite verification**: Execute pytest to verify that the pipeline connection succeeds without raising PipelineConnectError and that all tests pass successfully. (Target: `None`)

## 5. Educational Concepts
### Variadic Input Sockets
- **What is it:** Special input sockets in Haystack pipelines that can accept data from multiple upstream sender components simultaneously.
- **Why it matters:** Without variadic sockets, components like builders or joiners would be restricted to receiving input from a single source, limiting flexibility when combining multiple retrievers or data sources.
- **Connection to Issue:** The PromptBuilder's `documents` socket needs to be recognized or configured as variadic so that multiple retrievers can feed documents into it without triggering connection errors.

### Type Annotation Metadata in Haystack
- **What is it:** The mechanism by which Haystack inspects Python type hints (such as `Variadic[T]`) using typing metadata and annotations to configure runtime pipeline behavior.
- **Why it matters:** Pipeline connection validation relies entirely on inspecting component socket type hints during initialization to determine graph connectivity rules.
- **Connection to Issue:** Because template variables default to `Any`, they lack the metadata required for the pipeline builder to identify them as variadic, leading to strict single-connection enforcement.

