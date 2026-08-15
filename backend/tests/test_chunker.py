"""
GitNova v4.2 — Sprint 6 Code Chunking Engine Tests

Comprehensive test suite covering:
  - Deterministic chunk IDs and output consistency across runs
  - Nested Python classes and methods (Outer.Inner.method)
  - Async functions and decorated functions (@decorator async def)
  - Malformed syntax fallback to line chunker
  - Unsupported languages/extensions
  - Unicode character and emoji support
  - Oversized symbol sub-chunking
  - Documentation (Markdown headers) and Configuration chunking
  - Operational budget limits (token/byte caps & skipped file reporting)
"""

import pytest

from app.intelligence.ingestor import RepoDocument, RepoDocumentCorpus, StructuralMetrics
from app.intelligence.chunker import (
    ChunkConfig,
    InformationClass,
    categorize_information_class,
    chunk_repository_corpus,
    PythonASTChunker,
)


# ── Helper Fixtures ───────────────────────────────────────────────────────────

def make_sample_corpus(documents: list) -> RepoDocumentCorpus:
    metrics = StructuralMetrics(
        file_count=len(documents),
        directory_count=2,
        max_directory_depth=2,
        total_loc=sum(d.loc for d in documents),
    )
    return RepoDocumentCorpus(
        full_name="pallets/flask",
        metrics=metrics,
        documents=documents,
    )


# ── Information Class Categorization Tests ────────────────────────────────────

class TestCategorization:

    def test_documentation_categorization(self):
        assert categorize_information_class("README.md", "Markdown") == InformationClass.DOCUMENTATION
        assert categorize_information_class("docs/index.rst", "reStructuredText") == InformationClass.DOCUMENTATION
        assert categorize_information_class("CONTRIBUTING.md", "Markdown") == InformationClass.DOCUMENTATION
        assert categorize_information_class("assets/changelogs/1133.txt", "Text") == InformationClass.DOCUMENTATION
        assert categorize_information_class("CHANGELOG.md", "Markdown") == InformationClass.DOCUMENTATION
        assert categorize_information_class("docs/guide.txt", "Text") == InformationClass.DOCUMENTATION
        assert categorize_information_class("help/command.txt", "Plain Text") == InformationClass.DOCUMENTATION

    def test_configuration_categorization(self):
        assert categorize_information_class("pyproject.toml", "TOML") == InformationClass.CONFIGURATION
        assert categorize_information_class("package.json", "JSON") == InformationClass.CONFIGURATION
        assert categorize_information_class("Dockerfile", "Other") == InformationClass.CONFIGURATION
        assert categorize_information_class(".gitignore", "Other") == InformationClass.CONFIGURATION
        assert categorize_information_class(".gitattributes", "Other") == InformationClass.CONFIGURATION
        assert categorize_information_class(".editorconfig", "Other") == InformationClass.CONFIGURATION
        assert categorize_information_class(".dockerignore", "Other") == InformationClass.CONFIGURATION

    def test_tests_categorization(self):
        assert categorize_information_class("tests/test_app.py", "Python") == InformationClass.TESTS
        assert categorize_information_class("src/user_test.py", "Python") == InformationClass.TESTS
        assert categorize_information_class("test/widget_test.dart", "Dart") == InformationClass.TESTS

    def test_source_code_categorization(self):
        assert categorize_information_class("lib/main.dart", "Dart") == InformationClass.SOURCE_CODE
        assert categorize_information_class("src/app.py", "Python") == InformationClass.SOURCE_CODE
        assert categorize_information_class("src/index.js", "JavaScript") == InformationClass.SOURCE_CODE
        assert categorize_information_class("crates/main.rs", "Rust") == InformationClass.SOURCE_CODE
        assert categorize_information_class("lib/utils.ts", "TypeScript") == InformationClass.SOURCE_CODE


# ── Python AST Chunking Tests ─────────────────────────────────────────────────

class TestPythonASTChunker:

    def test_nested_classes_and_methods(self):
        code = """
class Outer:
    class Inner:
        def inner_method(self):
            return 42
"""
        doc = RepoDocument(
            file_path="C:/repo/src/nested.py",
            relative_path="src/nested.py",
            language="Python",
            loc=6,
            size_bytes=len(code),
            content=code,
        )
        chunker = PythonASTChunker()
        chunks = chunker.parse_and_chunk(doc, ChunkConfig(), "test/repo")
        assert chunks is not None

        qual_names = [c.qualified_symbol_name for c in chunks]
        assert "Outer" in qual_names
        assert "Outer.Inner" in qual_names
        assert "Outer.Inner.inner_method" in qual_names

        inner_method_chunk = next(c for c in chunks if c.symbol_name == "inner_method")
        assert inner_method_chunk.parent_symbol == "Outer.Inner"
        assert inner_method_chunk.symbol_type == "method"

    def test_async_and_decorated_functions(self):
        code = """
@pytest.fixture
@decorator_two(option=True)
async def fetch_data():
    \"\"\"Docstring here.\"\"\"
    await asyncio.sleep(1)
    return {"status": "ok"}
"""
        doc = RepoDocument(
            file_path="C:/repo/src/async_module.py",
            relative_path="src/async_module.py",
            language="Python",
            loc=7,
            size_bytes=len(code),
            content=code,
        )
        chunker = PythonASTChunker()
        chunks = chunker.parse_and_chunk(doc, ChunkConfig(), "test/repo")
        assert chunks is not None

        async_chunk = next(c for c in chunks if c.symbol_name == "fetch_data")
        assert async_chunk.symbol_type == "async_function"
        assert "@pytest.fixture" in async_chunk.raw_content
        assert async_chunk.start_line == 2  # Decorator start line

    def test_syntax_error_returns_none(self):
        code = "def broken_syntax((: invalid python code"
        doc = RepoDocument(
            file_path="C:/repo/src/broken.py",
            relative_path="src/broken.py",
            language="Python",
            loc=1,
            size_bytes=len(code),
            content=code,
        )
        chunker = PythonASTChunker()
        chunks = chunker.parse_and_chunk(doc, ChunkConfig(), "test/repo")
        assert chunks is None


# ── Oversized Symbol & Line Fallback Tests ────────────────────────────────────

class TestOversizedSymbols:

    def test_oversized_function_is_sub_chunked(self):
        """A monolithic function exceeding max_chunk_lines is sub-chunked."""
        body = "\n".join([f"    x_{i} = {i}" for i in range(200)])
        code = f"def monolithic_function():\n{body}\n"
        doc = RepoDocument(
            file_path="C:/repo/src/big.py",
            relative_path="src/big.py",
            language="Python",
            loc=202,
            size_bytes=len(code),
            content=code,
        )
        config = ChunkConfig(max_chunk_lines=50)
        chunker = PythonASTChunker()
        chunks = chunker.parse_and_chunk(doc, config, "test/repo")
        assert chunks is not None

        # Should produce multiple sub-chunks for monolithic_function
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.qualified_symbol_name == "monolithic_function"
            assert chunk.end_line - chunk.start_line + 1 <= 60


# ── Full Pipeline Orchestration Tests ─────────────────────────────────────────

class TestChunkPipeline:

    def test_deterministic_chunk_ids_and_output(self):
        doc1 = RepoDocument("C:/r/README.md", "README.md", "Markdown", 10, 100, "# Title\nSection 1\n")
        doc2 = RepoDocument("C:/r/src/app.py", "src/app.py", "Python", 5, 60, "def hello():\n    return 'hi'\n")
        corpus = make_sample_corpus([doc1, doc2])

        result1 = chunk_repository_corpus(corpus)
        result2 = chunk_repository_corpus(corpus)

        assert result1.total_chunks == result2.total_chunks
        assert [c.chunk_id for c in result1.chunks] == [c.chunk_id for c in result2.chunks]
        assert [c.contextual_header for c in result1.chunks] == [c.contextual_header for c in result2.chunks]

    def test_unsupported_language_uses_line_fallback(self):
        doc = RepoDocument("C:/r/script.xyz", "script.xyz", "UnknownLang", 10, 100, "line 1\nline 2\nline 3\n")
        corpus = make_sample_corpus([doc])
        result = chunk_repository_corpus(corpus)

        assert result.total_chunks == 1
        assert result.chunks[0].parser_strategy == "line_fallback"

    def test_unicode_and_emoji_handling(self):
        code = "# 日本語コメント 🚀\ndef greet():\n    return 'こんにちは世界'\n"
        doc = RepoDocument("C:/r/src/unicode.py", "src/unicode.py", "Python", 3, len(code.encode('utf-8')), code)
        corpus = make_sample_corpus([doc])
        result = chunk_repository_corpus(corpus)

        assert result.total_chunks >= 1
        assert "こんにちは世界" in result.chunks[0].raw_content

    def test_budget_exhaustion_reports_skipped_files(self):
        doc1 = RepoDocument("C:/r/src/app1.py", "src/app1.py", "Python", 2, 20, "def f1():\n    pass\n")
        doc2 = RepoDocument("C:/r/src/app2.py", "src/app2.py", "Python", 2, 20, "def f2():\n    pass\n")
        corpus = make_sample_corpus([doc1, doc2])

        # Restrict budget to 1 file limit
        tight_config = ChunkConfig(max_total_tokens=100, max_files=1)
        result = chunk_repository_corpus(corpus, tight_config)

        assert result.files_processed == 1
        assert result.files_skipped_budget == 1
        assert result.total_chunks >= 1


# ── Two-Stage Allocation & Token Bounding Tests ──────────────────────────────

class TestTwoStageAllocationAndBounding:

    def test_all_four_classes_present_initial_representation(self):
        """When all 4 classes have content, Stage 1 processes each class up to its initial allocation cap."""
        source_code = "def f():\n" + "    x = 1\n" * 5000
        docs_code = "# Guide\n" + "Doc line text.\n" * 5000
        tests_code = "def test_f():\n" + "    assert True\n" * 5000
        config_code = "key: value\n" + "item: 1\n" * 5000

        doc_src = RepoDocument("C:/r/src/main.py", "src/main.py", "Python", 5000, len(source_code), source_code)
        doc_doc = RepoDocument("C:/r/README.md", "README.md", "Markdown", 5000, len(docs_code), docs_code)
        doc_test = RepoDocument("C:/r/tests/test_main.py", "tests/test_main.py", "Python", 5000, len(tests_code), tests_code)
        doc_cfg = RepoDocument("C:/r/config.yaml", "config.yaml", "YAML", 5000, len(config_code), config_code)

        corpus = make_sample_corpus([doc_src, doc_doc, doc_test, doc_cfg])
        config = ChunkConfig(max_total_tokens=100_000, max_files=100)
        result = chunk_repository_corpus(corpus, config)

        assert result.total_tokens <= 100_000
        assert result.chunks_by_info_class[InformationClass.SOURCE_CODE] > 0
        assert result.chunks_by_info_class[InformationClass.DOCUMENTATION] > 0
        assert result.chunks_by_info_class[InformationClass.TESTS] > 0
        assert result.chunks_by_info_class[InformationClass.CONFIGURATION] > 0

    def test_absent_documentation_redistributes_to_source_and_tests(self):
        """When documentation is absent, its 15% allocation is redistributed in Stage 2."""
        source_code = "def f():\n" + "    x = 1\n" * 10000
        tests_code = "def test_f():\n" + "    assert True\n" * 10000

        doc_src = RepoDocument("C:/r/src/main.py", "src/main.py", "Python", 10000, len(source_code), source_code)
        doc_test = RepoDocument("C:/r/tests/test_main.py", "tests/test_main.py", "Python", 10000, len(tests_code), tests_code)

        corpus = make_sample_corpus([doc_src, doc_test])
        config = ChunkConfig(max_total_tokens=100_000, max_files=100)
        result = chunk_repository_corpus(corpus, config)

        assert result.total_tokens <= 100_000
        assert result.chunks_by_info_class[InformationClass.DOCUMENTATION] == 0
        assert result.chunks_by_info_class[InformationClass.SOURCE_CODE] > 0

    def test_huge_source_cannot_starve_docs_and_tests_in_stage1(self):
        """Huge source corpus cannot consume test/doc initial allocations before Stage 1 completes."""
        source_code = "def f():\n" + "    x = 1\n" * 20000
        docs_code = "# Documentation\n" + "Help text.\n" * 500
        tests_code = "def test_func():\n" + "    assert 1 == 1\n" * 500

        doc_src = RepoDocument("C:/r/src/huge.py", "src/huge.py", "Python", 20000, len(source_code), source_code)
        doc_doc = RepoDocument("C:/r/README.md", "README.md", "Markdown", 500, len(docs_code), docs_code)
        doc_test = RepoDocument("C:/r/tests/test_func.py", "tests/test_func.py", "Python", 500, len(tests_code), tests_code)

        corpus = make_sample_corpus([doc_src, doc_doc, doc_test])
        config = ChunkConfig(max_total_tokens=100_000, max_files=100)
        result = chunk_repository_corpus(corpus, config)

        assert result.chunks_by_info_class[InformationClass.DOCUMENTATION] > 0
        assert result.chunks_by_info_class[InformationClass.TESTS] > 0
        assert result.total_tokens <= 100_000

    def test_huge_documentation_cannot_starve_source_code(self):
        """Huge documentation corpus cannot consume source code initial allocation."""
        docs_code = "# Big Guide\n" + "Detailed docs.\n" * 20000
        source_code = "def core_logic():\n    return 42\n"

        doc_doc = RepoDocument("C:/r/README.md", "README.md", "Markdown", 20000, len(docs_code), docs_code)
        doc_src = RepoDocument("C:/r/src/core.py", "src/core.py", "Python", 2, len(source_code), source_code)

        corpus = make_sample_corpus([doc_doc, doc_src])
        config = ChunkConfig(max_total_tokens=100_000, max_files=100)
        result = chunk_repository_corpus(corpus, config)

        assert result.chunks_by_info_class[InformationClass.SOURCE_CODE] > 0
        assert result.total_tokens <= 100_000

    def test_total_tokens_never_exceeds_max_total_tokens(self):
        """Final total token count mathematically never exceeds max_total_tokens."""
        docs = [
            RepoDocument(f"C:/r/src/file_{i}.py", f"src/file_{i}.py", "Python", 500, 5000, "def f():\n" + "    pass\n" * 100)
            for i in range(50)
        ]
        corpus = make_sample_corpus(docs)
        config = ChunkConfig(max_total_tokens=25_000, max_files=100)
        result = chunk_repository_corpus(corpus, config)

        assert result.total_tokens <= 25_000

    def test_single_chunk_token_bounds_strictly_enforced(self):
        """Every single chunk emitted is <= max_chunk_tokens (1,500 tokens)."""
        single_long_line = "x = " + "'a' * 30000\n"
        doc = RepoDocument("C:/r/src/long_line.py", "src/long_line.py", "Python", 1, len(single_long_line), single_long_line)
        corpus = make_sample_corpus([doc])
        config = ChunkConfig(max_chunk_tokens=1500)
        result = chunk_repository_corpus(corpus, config)

        for chunk in result.chunks:
            assert chunk.token_estimate <= 1500
