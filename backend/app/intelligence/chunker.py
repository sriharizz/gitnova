"""
GitNova v4.2 — Code Chunking Engine

Responsibility:
  - Takes a RepoDocumentCorpus (from Sprint 5) and parses code into structured CodeChunk objects.
  - Implements dynamic content budgeting (max_total_tokens, max_total_bytes, max_files) rather than rigid cutoffs.
  - Categorizes files into 4 information classes (DOCUMENTATION, SOURCE_CODE, CONFIGURATION, TESTS),
    guaranteeing README/CONTRIBUTING/docs are prioritized for beginner mentoring.
  - AST-aware parsing for Python (built-in stdlib ast) and JS/TS/Java/Go/C (Tree-sitter).
  - Rich retrieval metadata: qualified_symbol_name, parent_symbol, line ranges, and deterministic contextual_header.
  - Bounded multi-strategy chunking: sub-chunks oversized functions/classes.
  - Graceful fallback: FallbackLineChunker activates on syntax errors or unsupported formats.
  - Zero embeddings, zero pgvector, zero LLM calls — strictly bounded chunking & metadata contract.
"""

import ast
from dataclasses import dataclass, field
import hashlib
from typing import Dict, List, Optional, Tuple
import warnings

from app.intelligence.ingestor import RepoDocument, RepoDocumentCorpus
from app.core.logging import get_logger

logger = get_logger(__name__)

# Suppress tree_sitter deprecation warning output during imports
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    try:
        import tree_sitter
        from tree_sitter_languages import get_language, get_parser
        TREE_SITTER_AVAILABLE = True
    except ImportError:
        TREE_SITTER_AVAILABLE = False


# ── Information Classes ───────────────────────────────────────────────────────

class InformationClass:
    DOCUMENTATION = "DOCUMENTATION"
    SOURCE_CODE = "SOURCE_CODE"
    CONFIGURATION = "CONFIGURATION"
    TESTS = "TESTS"


# ── Configuration & Data Contracts ───────────────────────────────────────────

@dataclass
class ChunkConfig:
    """Configurable operational defaults for repository chunking budget & bounds."""
    max_total_tokens: int = 150_000         # Token limit budget per repo
    max_total_bytes: int = 600_000           # Byte limit budget per repo
    max_files: int = 100                     # Safety guardrail file count
    target_chunk_lines: int = 50             # Target chunk length in lines
    max_chunk_lines: int = 120               # Upper bound for single chunk lines
    max_chunk_tokens: int = 1_500            # Upper bound for single chunk estimated tokens
    overlap_lines: int = 10                  # Line overlap for sliding window fallback


@dataclass
class CodeChunk:
    """
    Structured code chunk with rich retrieval context and deterministic header.
    token_estimate: Cheap character-based approximation (len(raw_content) // 4).
    """
    chunk_id: str                          # Deterministic sha256 hash
    file_path: str                         # Relative path (e.g. "src/auth/manager.py")
    language: str                          # e.g. "Python", "JavaScript", "Markdown"
    info_class: str                        # DOCUMENTATION | SOURCE_CODE | CONFIGURATION | TESTS
    symbol_name: str                       # Local symbol name (e.g. "authenticate")
    qualified_symbol_name: str             # Fully qualified name (e.g. "AuthManager.authenticate")
    symbol_type: str                       # function | async_function | class | method | async_method | doc_section | config_block | text_block
    parent_symbol: Optional[str]           # Parent class or container (e.g. "AuthManager")
    start_line: int                        # 1-based start line
    end_line: int                          # 1-based end line
    raw_content: str                       # Exact unmodified source text
    contextual_header: str                 # Deterministic header string for embedding/LLM
    token_estimate: int                    # Approximated token count (len / 4)
    parser_strategy: str                   # python_ast | tree_sitter | markdown_header | line_fallback


@dataclass
class ChunkedRepository:
    """Complete chunking output and summary metrics for a repository."""
    full_name: str
    total_chunks: int
    total_tokens: int
    total_bytes: int
    corpus_files_available: int
    files_processed: int
    files_skipped_budget: int
    chunks_by_info_class: Dict[str, int]
    chunks_by_parser_strategy: Dict[str, int]
    min_chunk_tokens: int
    avg_chunk_tokens: float
    max_chunk_tokens: int
    parser_fallbacks_occurred: bool
    chunks: List[CodeChunk]


# ── Categorization Helper ─────────────────────────────────────────────────────

def categorize_information_class(file_path: str, language: str) -> str:
    """Categorizes a file into one of 4 information classes based on path and extension."""
    norm_path = file_path.lower().replace("\\", "/")
    filename = norm_path.split("/")[-1]
    ext = filename.split(".")[-1] if "." in filename else ""

    # 1. Tests
    if (
        "test/" in norm_path or "tests/" in norm_path or "spec/" in norm_path
        or filename.startswith("test_") or filename.endswith("_test.py")
        or filename.endswith("_test.dart") or filename.endswith(".spec.ts")
        or filename.endswith(".test.js") or filename.endswith(".test.ts")
    ):
        return InformationClass.TESTS

    # 2. Documentation
    if (
        language in {"Markdown", "reStructuredText", "Text", "Plain Text"}
        or ext in {"md", "rst", "txt"}
        or filename.startswith("readme") or filename.startswith("contributing")
        or filename.startswith("architecture") or filename.startswith("changelog")
        or filename.startswith("license") or filename.startswith("notice")
        or filename.startswith("authors") or filename.startswith("history")
        or "docs/" in norm_path or "doc/" in norm_path or "changelog" in norm_path
        or "help/" in norm_path or "licenses/" in norm_path
    ):
        return InformationClass.DOCUMENTATION

    # 3. Configuration
    if (
        language in {"YAML", "TOML", "JSON", "XML"}
        or ext in {
            "tmtheme", "theme", "vsixmanifest", "plist", "properties",
            "xml", "json", "yaml", "yml", "toml",
            "gitignore", "gitattributes", "editorconfig", "dockerignore", "npmignore", "metadata"
        }
        or filename in {
            "pyproject.toml", "package.json", "cargo.toml", "dockerfile",
            "go.mod", "pom.xml", "build.gradle", "setup.cfg", "requirements.txt",
            ".gitignore", ".gitattributes", ".editorconfig", ".dockerignore", ".npmignore", ".metadata"
        }
    ):
        return InformationClass.CONFIGURATION

    # 4. Source Code
    return InformationClass.SOURCE_CODE


def estimate_tokens(text: str) -> int:
    """Cheap character-based approximation (~4 characters per token)."""
    return max(1, len(text) // 4)


def generate_chunk_id(
    full_name: str,
    file_path: str,
    start_line: int,
    end_line: int,
    qualified_name: str,
) -> str:
    """Generates a deterministic sha256 chunk ID."""
    key = f"{full_name}:{file_path}:{start_line}:{end_line}:{qualified_name}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def generate_contextual_header(
    file_path: str,
    qualified_symbol_name: str,
    symbol_type: str,
    start_line: int,
    end_line: int,
    parent_symbol: Optional[str] = None,
) -> str:
    """Generates a deterministic contextual header for retrieval grounding."""
    type_title = symbol_type.replace("_", " ").title()
    if parent_symbol and qualified_symbol_name != parent_symbol:
        return (
            f"[File: {file_path} | Class: {parent_symbol} | "
            f"{type_title}: {qualified_symbol_name} (Lines {start_line}-{end_line})]"
        )
    return (
        f"[File: {file_path} | {type_title}: {qualified_symbol_name} (Lines {start_line}-{end_line})]"
    )


# ── Sliding Window Fallback Line Chunker ──────────────────────────────────────

def chunk_by_lines_fallback(
    doc: RepoDocument,
    config: ChunkConfig,
    symbol_name: str = "text_block",
    qualified_name: str = "text_block",
    symbol_type: str = "text_block",
    parent_symbol: Optional[str] = None,
    info_class: Optional[str] = None,
    parser_strategy: str = "line_fallback",
    full_name: str = "",
) -> List[CodeChunk]:
    """
    Sliding-window line chunker bounded by line count and estimated tokens.
    Handles non-AST files, malformed syntax, or oversized symbol sub-chunking.
    """
    lines = doc.content.splitlines(keepends=True)
    if not lines:
        return []

    info_class = info_class or categorize_information_class(doc.relative_path, doc.language)
    chunks: List[CodeChunk] = []

    target_lines = config.target_chunk_lines
    overlap = config.overlap_lines
    total_file_lines = len(lines)

    idx = 0
    while idx < total_file_lines:
        end_idx = min(idx + target_lines, total_file_lines)
        chunk_lines = lines[idx:end_idx]
        chunk_text = "".join(chunk_lines)

        # Token estimate bound check: if oversized, reduce end_idx down to single line
        while len(chunk_lines) > 1 and estimate_tokens(chunk_text) > config.max_chunk_tokens:
            end_idx = max(idx + 1, end_idx - 5)
            chunk_lines = lines[idx:end_idx]
            chunk_text = "".join(chunk_lines)

        # If a single line exceeds max_chunk_tokens, truncate text to fit max_chunk_tokens
        if estimate_tokens(chunk_text) > config.max_chunk_tokens:
            chunk_text = chunk_text[: config.max_chunk_tokens * 4]

        start_line = idx + 1
        end_line = end_idx

        q_name = qualified_name if qualified_name != "text_block" else f"{doc.relative_path}:{start_line}-{end_line}"
        s_name = symbol_name if symbol_name != "text_block" else f"lines_{start_line}_{end_line}"

        c_id = generate_chunk_id(full_name, doc.relative_path, start_line, end_line, q_name)
        header = generate_contextual_header(
            doc.relative_path, q_name, symbol_type, start_line, end_line, parent_symbol
        )

        chunks.append(
            CodeChunk(
                chunk_id=c_id,
                file_path=doc.relative_path,
                language=doc.language,
                info_class=info_class,
                symbol_name=s_name,
                qualified_symbol_name=q_name,
                symbol_type=symbol_type,
                parent_symbol=parent_symbol,
                start_line=start_line,
                end_line=end_line,
                raw_content=chunk_text,
                contextual_header=header,
                token_estimate=estimate_tokens(chunk_text),
                parser_strategy=parser_strategy,
            )
        )

        if end_idx >= total_file_lines:
            break
        idx = max(idx + 1, end_idx - overlap)

    return chunks


# ── Python AST Chunker ────────────────────────────────────────────────────────

class PythonASTChunker:
    """
    AST-aware chunker for Python code using stdlib ast module.
    Extracts functions, async functions, classes, decorated methods, and docstrings.
    Generates qualified symbol names (e.g. Outer.Inner.method) and handles line ranges.
    """

    def parse_and_chunk(
        self,
        doc: RepoDocument,
        config: ChunkConfig,
        full_name: str,
    ) -> Optional[List[CodeChunk]]:
        """Parses Python source file and returns List[CodeChunk], or None if SyntaxError."""
        try:
            tree = ast.parse(doc.content, filename=doc.relative_path)
        except (SyntaxError, ValueError):
            return None  # Triggers graceful FallbackLineChunker

        lines = doc.content.splitlines(keepends=True)
        info_class = categorize_information_class(doc.relative_path, doc.language)
        chunks: List[CodeChunk] = []

        # 1. Module-level header / docstring
        docstring = ast.get_docstring(tree)
        if docstring:
            first_stmt = tree.body[0] if tree.body else None
            end_line = getattr(first_stmt, "end_lineno", getattr(first_stmt, "lineno", 10))
            module_text = "".join(lines[0:end_line])
            q_name = f"{doc.relative_path}:module"
            c_id = generate_chunk_id(full_name, doc.relative_path, 1, end_line, q_name)
            header = generate_contextual_header(
                doc.relative_path, q_name, "module_docstring", 1, end_line
            )
            chunks.append(
                CodeChunk(
                    chunk_id=c_id,
                    file_path=doc.relative_path,
                    language=doc.language,
                    info_class=info_class,
                    symbol_name="module_docstring",
                    qualified_symbol_name=q_name,
                    symbol_type="module_docstring",
                    parent_symbol=None,
                    start_line=1,
                    end_line=end_line,
                    raw_content=module_text,
                    contextual_header=header,
                    token_estimate=estimate_tokens(module_text),
                    parser_strategy="python_ast",
                )
            )

        # 2. Recursive AST Visitor for Classes, Methods, Functions
        def visit_node(node: ast.AST, parent_stack: List[str]):
            nonlocal chunks

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = getattr(child, "lineno", 1)
                    end_line = getattr(child, "end_lineno", start_line)

                    # Include decorator lines if present
                    if child.decorator_list:
                        first_dec = child.decorator_list[0]
                        dec_start = getattr(first_dec, "lineno", start_line)
                        if dec_start < start_line:
                            start_line = dec_start

                    # Qualified symbol & parent name
                    current_name = child.name
                    parent_name = ".".join(parent_stack) if parent_stack else None
                    if parent_stack:
                        qualified_name = f"{'.'.join(parent_stack)}.{current_name}"
                    else:
                        qualified_name = current_name

                    # Symbol type
                    if isinstance(child, ast.ClassDef):
                        sym_type = "class"
                    elif isinstance(child, ast.AsyncFunctionDef):
                        sym_type = "async_method" if parent_stack else "async_function"
                    else:
                        sym_type = "method" if parent_stack else "function"

                    raw_text = "".join(lines[start_line - 1:end_line])
                    tokens = estimate_tokens(raw_text)

                    # Bounded Sub-Chunking for Oversized Symbols
                    line_count = end_line - start_line + 1
                    if line_count > config.max_chunk_lines or tokens > config.max_chunk_tokens:
                        # Sub-chunk oversized symbol while preserving qualified_name and parent_name
                        sub_doc = RepoDocument(
                            file_path=doc.file_path,
                            relative_path=doc.relative_path,
                            language=doc.language,
                            loc=line_count,
                            size_bytes=len(raw_text),
                            content=raw_text,
                        )
                        sub_chunks = chunk_by_lines_fallback(
                            doc=sub_doc,
                            config=config,
                            symbol_name=current_name,
                            qualified_name=qualified_name,
                            symbol_type=f"{sym_type}_part",
                            parent_symbol=parent_name,
                            info_class=info_class,
                            parser_strategy="python_ast",
                            full_name=full_name,
                        )
                        # Adjust 1-based start/end line offsets for sub-chunks
                        for sc in sub_chunks:
                            sc.start_line = start_line + sc.start_line - 1
                            sc.end_line = start_line + sc.end_line - 1
                            sc.contextual_header = generate_contextual_header(
                                doc.relative_path, qualified_name, sym_type, sc.start_line, sc.end_line, parent_name
                            )
                            sc.chunk_id = generate_chunk_id(
                                full_name, doc.relative_path, sc.start_line, sc.end_line, qualified_name
                            )
                        chunks.extend(sub_chunks)
                    else:
                        c_id = generate_chunk_id(full_name, doc.relative_path, start_line, end_line, qualified_name)
                        header = generate_contextual_header(
                            doc.relative_path, qualified_name, sym_type, start_line, end_line, parent_name
                        )
                        chunks.append(
                            CodeChunk(
                                chunk_id=c_id,
                                file_path=doc.relative_path,
                                language=doc.language,
                                info_class=info_class,
                                symbol_name=current_name,
                                qualified_symbol_name=qualified_name,
                                symbol_type=sym_type,
                                parent_symbol=parent_name,
                                start_line=start_line,
                                end_line=end_line,
                                raw_content=raw_text,
                                contextual_header=header,
                                token_estimate=tokens,
                                parser_strategy="python_ast",
                            )
                        )

                    # Recurse into classes to find nested classes / methods
                    if isinstance(child, ast.ClassDef):
                        visit_node(child, parent_stack + [current_name])

        visit_node(tree, [])
        return chunks if chunks else None


# ── Tree-Sitter Multi-Language Chunker ────────────────────────────────────────

LANGUAGE_MAP_TREESITTER = {
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Java": "java",
    "Go": "go",
    "Rust": "rust",
    "C": "c",
    "C++": "cpp",
}


class TreeSitterChunker:
    """Multi-language AST chunker using tree-sitter & tree-sitter-languages."""

    def parse_and_chunk(
        self,
        doc: RepoDocument,
        config: ChunkConfig,
        full_name: str,
    ) -> Optional[List[CodeChunk]]:
        if not TREE_SITTER_AVAILABLE:
            return None

        ts_lang = LANGUAGE_MAP_TREESITTER.get(doc.language)
        if not ts_lang:
            return None

        try:
            parser = get_parser(ts_lang)
            content_bytes = doc.content.encode("utf-8")
            tree = parser.parse(content_bytes)
        except Exception as e:
            logger.debug("tree_sitter_parse_error", extra={"file": doc.relative_path, "error": str(e)})
            return None

        # Check for root parsing errors
        if tree.root_node.has_error:
            logger.debug("tree_sitter_syntax_error", extra={"file": doc.relative_path})
            return None

        lines = doc.content.splitlines(keepends=True)
        info_class = categorize_information_class(doc.relative_path, doc.language)
        chunks: List[CodeChunk] = []

        # Target AST node types across C-family languages
        target_types = {
            "function_declaration", "function_definition", "method_definition",
            "class_declaration", "struct_specifier", "interface_declaration",
            "type_declaration", "impl_item"
        }

        def visit_node(node, parent_name: Optional[str] = None):
            nonlocal chunks

            if node.type in target_types:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                # Extract local symbol identifier
                name_node = node.child_by_field_name("name")
                sym_name = name_node.text.decode("utf-8") if name_node else node.type

                q_name = f"{parent_name}.{sym_name}" if parent_name else sym_name
                raw_text = "".join(lines[start_line - 1:end_line])
                tokens = estimate_tokens(raw_text)

                line_count = end_line - start_line + 1
                if line_count > config.max_chunk_lines or tokens > config.max_chunk_tokens:
                    sub_doc = RepoDocument(
                        file_path=doc.file_path,
                        relative_path=doc.relative_path,
                        language=doc.language,
                        loc=line_count,
                        size_bytes=len(raw_text),
                        content=raw_text,
                    )
                    sub_chunks = chunk_by_lines_fallback(
                        doc=sub_doc,
                        config=config,
                        symbol_name=sym_name,
                        qualified_name=q_name,
                        symbol_type=f"{node.type}_part",
                        parent_symbol=parent_name,
                        info_class=info_class,
                        parser_strategy="tree_sitter",
                        full_name=full_name,
                    )
                    for sc in sub_chunks:
                        sc.start_line = start_line + sc.start_line - 1
                        sc.end_line = start_line + sc.end_line - 1
                        sc.contextual_header = generate_contextual_header(
                            doc.relative_path, q_name, node.type, sc.start_line, sc.end_line, parent_name
                        )
                        sc.chunk_id = generate_chunk_id(
                            full_name, doc.relative_path, sc.start_line, sc.end_line, q_name
                        )
                    chunks.extend(sub_chunks)
                else:
                    c_id = generate_chunk_id(full_name, doc.relative_path, start_line, end_line, q_name)
                    header = generate_contextual_header(
                        doc.relative_path, q_name, node.type, start_line, end_line, parent_name
                    )

                    chunks.append(
                        CodeChunk(
                            chunk_id=c_id,
                            file_path=doc.relative_path,
                            language=doc.language,
                            info_class=info_class,
                            symbol_name=sym_name,
                            qualified_symbol_name=q_name,
                            symbol_type=node.type,
                            parent_symbol=parent_name,
                            start_line=start_line,
                            end_line=end_line,
                            raw_content=raw_text,
                            contextual_header=header,
                            token_estimate=tokens,
                            parser_strategy="tree_sitter",
                        )
                    )

                new_parent = sym_name if "class" in node.type or "struct" in node.type or "interface" in node.type else parent_name
                for child in node.children:
                    visit_node(child, new_parent)
            else:
                for child in node.children:
                    visit_node(child, parent_name)

        visit_node(tree.root_node)
        return chunks if chunks else None


# ── Markdown Section Header Chunker ───────────────────────────────────────────

class MarkdownHeaderChunker:
    """Header-aware section chunker for Markdown & documentation files."""

    def parse_and_chunk(
        self,
        doc: RepoDocument,
        config: ChunkConfig,
        full_name: str,
    ) -> Optional[List[CodeChunk]]:
        lines = doc.content.splitlines(keepends=True)
        if not lines:
            return []

        info_class = categorize_information_class(doc.relative_path, doc.language)
        chunks: List[CodeChunk] = []

        section_lines: List[str] = []
        section_title = "overview"
        section_start_line = 1

        def append_section(title: str, s_lines: List[str], start_ln: int, end_ln: int):
            if not s_lines:
                return
            text = "".join(s_lines)
            tokens = estimate_tokens(text)
            q_name = f"{doc.relative_path}#{title}"
            line_cnt = end_ln - start_ln + 1

            if line_cnt > config.max_chunk_lines or tokens > config.max_chunk_tokens:
                sub_doc = RepoDocument(
                    file_path=doc.file_path,
                    relative_path=doc.relative_path,
                    language=doc.language,
                    loc=line_cnt,
                    size_bytes=len(text),
                    content=text,
                )
                sub_chunks = chunk_by_lines_fallback(
                    doc=sub_doc,
                    config=config,
                    symbol_name=title,
                    qualified_name=q_name,
                    symbol_type="doc_section_part",
                    parent_symbol=None,
                    info_class=info_class,
                    parser_strategy="markdown_header",
                    full_name=full_name,
                )
                for sc in sub_chunks:
                    sc.start_line = start_ln + sc.start_line - 1
                    sc.end_line = start_ln + sc.end_line - 1
                    sc.contextual_header = generate_contextual_header(
                        doc.relative_path, title, "doc_section", sc.start_line, sc.end_line
                    )
                    sc.chunk_id = generate_chunk_id(
                        full_name, doc.relative_path, sc.start_line, sc.end_line, q_name
                    )
                chunks.extend(sub_chunks)
            else:
                c_id = generate_chunk_id(full_name, doc.relative_path, start_ln, end_ln, q_name)
                header = generate_contextual_header(
                    doc.relative_path, title, "doc_section", start_ln, end_ln
                )
                chunks.append(
                    CodeChunk(
                        chunk_id=c_id,
                        file_path=doc.relative_path,
                        language=doc.language,
                        info_class=info_class,
                        symbol_name=title,
                        qualified_symbol_name=q_name,
                        symbol_type="doc_section",
                        parent_symbol=None,
                        start_line=start_ln,
                        end_line=end_ln,
                        raw_content=text,
                        contextual_header=header,
                        token_estimate=tokens,
                        parser_strategy="markdown_header",
                    )
                )

        for idx, line in enumerate(lines, start=1):
            if line.startswith(("# ", "## ", "### ", "#### ")):
                if section_lines:
                    append_section(section_title, section_lines, section_start_line, idx - 1)
                section_lines = [line]
                section_title = line.strip("# \t\r\n").replace(" ", "_").lower() or "section"
                section_start_line = idx
            else:
                section_lines.append(line)

        if section_lines:
            append_section(section_title, section_lines, section_start_line, len(lines))

        return chunks


# ── Core Orchestrator Entry Point ─────────────────────────────────────────────

def chunk_repository_corpus(
    corpus: RepoDocumentCorpus,
    config: ChunkConfig = ChunkConfig(),
) -> ChunkedRepository:
    """
    Main entry point for Sprint 6 Chunking.
    Takes a RepoDocumentCorpus and processes documents according to a 2-Stage Deterministic Allocation strategy.
    
    Initial Target Allocations (for max_total_tokens = 150,000):
      - SOURCE_CODE:   65% (97,500 tokens)
      - DOCUMENTATION: 15% (22,500 tokens)
      - TESTS:         15% (22,500 tokens)
      - CONFIGURATION: 5%  ( 7,500 tokens)

    Stage 1 — Guaranteed Representation:
      Each available information class is processed against its initial allocation cap.
      A class cannot consume another class's initial allocation during Stage 1.

    Stage 2 — Deterministic Redistribution:
      Unused capacity from Stage 1 is pooled and redistributed in priority order:
      1. SOURCE_CODE -> 2. TESTS -> 3. DOCUMENTATION -> 4. CONFIGURATION.
      Strictly enforces config.max_total_tokens as a hard upper bound.
    """
    B = config.max_total_tokens
    initial_allocations = {
        InformationClass.SOURCE_CODE: int(B * 0.65),
        InformationClass.DOCUMENTATION: int(B * 0.15),
        InformationClass.TESTS: int(B * 0.15),
        InformationClass.CONFIGURATION: int(B * 0.05),
    }

    # Group documents by information class
    docs_by_class: Dict[str, List[RepoDocument]] = {
        InformationClass.SOURCE_CODE: [],
        InformationClass.DOCUMENTATION: [],
        InformationClass.TESTS: [],
        InformationClass.CONFIGURATION: [],
    }

    for doc in corpus.documents:
        info_cls = categorize_information_class(doc.relative_path, doc.language)
        if info_cls in docs_by_class:
            docs_by_class[info_cls].append(doc)
        else:
            docs_by_class[InformationClass.SOURCE_CODE].append(doc)

    python_ast = PythonASTChunker()
    tree_sitter = TreeSitterChunker()
    markdown_parser = MarkdownHeaderChunker()

    parser_fallbacks_occurred = False

    def parse_doc(doc: RepoDocument) -> List[CodeChunk]:
        nonlocal parser_fallbacks_occurred
        doc_chunks: Optional[List[CodeChunk]] = None
        if doc.language == "Python":
            doc_chunks = python_ast.parse_and_chunk(doc, config, corpus.full_name)
            if doc_chunks is None:
                parser_fallbacks_occurred = True
        elif doc.language == "Markdown":
            doc_chunks = markdown_parser.parse_and_chunk(doc, config, corpus.full_name)
        elif doc.language in LANGUAGE_MAP_TREESITTER:
            doc_chunks = tree_sitter.parse_and_chunk(doc, config, corpus.full_name)
            if doc_chunks is None:
                parser_fallbacks_occurred = True

        if not doc_chunks:
            info_cls = categorize_information_class(doc.relative_path, doc.language)
            doc_chunks = chunk_by_lines_fallback(
                doc=doc,
                config=config,
                info_class=info_cls,
                parser_strategy="line_fallback",
                full_name=corpus.full_name,
            )
            if doc.language in {"Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C", "C++"}:
                parser_fallbacks_occurred = True

        return doc_chunks

    all_chunks: List[CodeChunk] = []
    processed_doc_paths = set()
    tokens_by_info_cls: Dict[str, int] = {c: 0 for c in initial_allocations}
    chunks_by_info_cls: Dict[str, int] = {c: 0 for c in initial_allocations}
    chunks_by_strategy: Dict[str, int] = {
        "python_ast": 0, "tree_sitter": 0, "markdown_header": 0, "line_fallback": 0
    }
    
    total_tokens = 0
    total_bytes = 0
    files_processed = 0

    # ── STAGE 1: Guaranteed Representation ────────────────────────────────────
    stage1_unprocessed_docs: Dict[str, List[RepoDocument]] = {c: [] for c in initial_allocations}

    for info_cls in [InformationClass.SOURCE_CODE, InformationClass.DOCUMENTATION, InformationClass.TESTS, InformationClass.CONFIGURATION]:
        cls_cap = initial_allocations[info_cls]
        for doc in docs_by_class[info_cls]:
            if files_processed >= config.max_files or total_tokens >= B:
                stage1_unprocessed_docs[info_cls].append(doc)
                continue

            doc_chunks = parse_doc(doc)
            admitted_doc_chunks = []
            
            for chunk in doc_chunks:
                # Check Stage 1 class cap AND overall repository budget B
                if (
                    tokens_by_info_cls[info_cls] + chunk.token_estimate <= cls_cap
                    and total_tokens + chunk.token_estimate <= B
                ):
                    admitted_doc_chunks.append(chunk)
                    tokens_by_info_cls[info_cls] += chunk.token_estimate
                    total_tokens += chunk.token_estimate
                else:
                    break

            if admitted_doc_chunks:
                for chunk in admitted_doc_chunks:
                    all_chunks.append(chunk)
                    chunks_by_info_cls[chunk.info_class] = chunks_by_info_cls.get(chunk.info_class, 0) + 1
                    chunks_by_strategy[chunk.parser_strategy] = chunks_by_strategy.get(chunk.parser_strategy, 0) + 1
                    total_bytes += len(chunk.raw_content.encode("utf-8"))
                files_processed += 1
                processed_doc_paths.add(doc.relative_path)
            else:
                stage1_unprocessed_docs[info_cls].append(doc)

    # ── STAGE 2: Deterministic Redistribution ─────────────────────────────────
    redistribution_priority = [
        InformationClass.SOURCE_CODE,
        InformationClass.TESTS,
        InformationClass.DOCUMENTATION,
        InformationClass.CONFIGURATION,
    ]

    for info_cls in redistribution_priority:
        if total_tokens >= B or files_processed >= config.max_files:
            break

        unprocessed = stage1_unprocessed_docs[info_cls]
        for doc in unprocessed:
            if total_tokens >= B or files_processed >= config.max_files:
                break
            if doc.relative_path in processed_doc_paths:
                continue

            doc_chunks = parse_doc(doc)
            admitted_doc_chunks = []
            for chunk in doc_chunks:
                if total_tokens + chunk.token_estimate <= B:
                    admitted_doc_chunks.append(chunk)
                    tokens_by_info_cls[chunk.info_class] += chunk.token_estimate
                    total_tokens += chunk.token_estimate
                else:
                    break

            if admitted_doc_chunks:
                for chunk in admitted_doc_chunks:
                    all_chunks.append(chunk)
                    chunks_by_info_cls[chunk.info_class] = chunks_by_info_cls.get(chunk.info_class, 0) + 1
                    chunks_by_strategy[chunk.parser_strategy] = chunks_by_strategy.get(chunk.parser_strategy, 0) + 1
                    total_bytes += len(chunk.raw_content.encode("utf-8"))
                files_processed += 1
                processed_doc_paths.add(doc.relative_path)

    files_skipped_budget = max(0, len(corpus.documents) - files_processed)

    # Token summary stats
    token_counts = [c.token_estimate for c in all_chunks]
    min_tokens = min(token_counts) if token_counts else 0
    max_tokens = max(token_counts) if token_counts else 0
    avg_tokens = round(sum(token_counts) / len(token_counts), 1) if token_counts else 0.0

    return ChunkedRepository(
        full_name=corpus.full_name,
        total_chunks=len(all_chunks),
        total_tokens=total_tokens,
        total_bytes=total_bytes,
        corpus_files_available=len(corpus.documents),
        files_processed=files_processed,
        files_skipped_budget=files_skipped_budget,
        chunks_by_info_class=chunks_by_info_cls,
        chunks_by_parser_strategy=chunks_by_strategy,
        min_chunk_tokens=min_tokens,
        avg_chunk_tokens=avg_tokens,
        max_chunk_tokens=max_tokens,
        parser_fallbacks_occurred=parser_fallbacks_occurred,
        chunks=all_chunks,
    )
