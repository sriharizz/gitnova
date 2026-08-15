"""
GitNova v4.2 — Sprint 5 Ingestion & Security Tests

Comprehensive tests covering:
  - Tar-Slip path traversal attack prevention
  - Archive download/extracted payload size limits
  - Archive file count limits
  - Symlink skipping
  - Binary file detection & skipping
  - Noise directory / vendor filtering (.git, node_modules, dist, lockfiles)
  - Structural metrics calculation (file count, total LOC, max directory depth)
  - Guaranteed temporary workspace cleanup
  - Structural onboarding complexity refinement
"""

import io
import pathlib
import tarfile
import tempfile
import pytest

from app.intelligence.ingestor import (
    ArchiveSecurityConfig,
    TarSlipSecurityException,
    ArchiveLimitExceededException,
    SecurityException,
    is_safe_tar_member,
    is_binary_content,
    unpack_tarball_safely,
    analyze_and_build_corpus,
    ingest_repository_archive,
    FileFilter,
)
from app.intelligence.scorer import RepositoryScorer


# ── Helpers for Building In-Memory Tarball Payloads ───────────────────────────

def create_mock_tarball(files_dict: dict, symlinks_dict: dict = None) -> bytes:
    """Helper to create a gzipped tarball in memory from a filename -> content dict."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files_dict.items():
            if isinstance(content, str):
                data = content.encode("utf-8")
            else:
                data = content
            ti = tarfile.TarInfo(name=name)
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))

        if symlinks_dict:
            for link_name, target in symlinks_dict.items():
                ti = tarfile.TarInfo(name=link_name)
                ti.type = tarfile.SYMTYPE
                ti.linkname = target
                tar.addfile(ti)

    return buf.getvalue()


# ── Security Tests ────────────────────────────────────────────────────────────

class TestArchiveSecurity:

    def test_tar_slip_path_traversal_prevention(self):
        """Tar-Slip: Archive member with path outside sandbox must be rejected."""
        base_dir = pathlib.Path(tempfile.mkdtemp())
        malicious_member = tarfile.TarInfo(name="../escape_sandbox.txt")

        assert not is_safe_tar_member(base_dir, malicious_member)

    def test_tar_slip_unpacks_safely_raises_exception(self):
        """Unpacking a malicious tarball raises TarSlipSecurityException."""
        payload = create_mock_tarball({
            "repo-main/app.py": "print('ok')",
            "../hacked.txt": "evil content",
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir)
            with pytest.raises(TarSlipSecurityException) as exc_info:
                unpack_tarball_safely(payload, target)
            assert "path traversal detected" in str(exc_info.value)

    def test_max_download_bytes_limit(self):
        """Payload exceeding max_download_bytes triggers ArchiveLimitExceededException."""
        payload = b"X" * 1000
        config = ArchiveSecurityConfig(max_download_bytes=500)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir)
            with pytest.raises(ArchiveLimitExceededException) as exc_info:
                unpack_tarball_safely(payload, target, security_config=config)
            assert "download limit" in str(exc_info.value)

    def test_max_file_count_limit(self):
        """Payload with too many files triggers ArchiveLimitExceededException."""
        files = {f"repo-main/file_{i}.txt": f"line {i}" for i in range(15)}
        payload = create_mock_tarball(files)
        config = ArchiveSecurityConfig(max_file_count=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir)
            with pytest.raises(ArchiveLimitExceededException) as exc_info:
                unpack_tarball_safely(payload, target, security_config=config)
            assert "file count limit" in str(exc_info.value)

    def test_symlink_skipping(self):
        """Symlinks in tarballs are safely skipped during extraction."""
        payload = create_mock_tarball(
            files_dict={"repo-main/app.py": "print('hello')"},
            symlinks_dict={"repo-main/app_link.py": "app.py"},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir)
            root = unpack_tarball_safely(payload, target)
            extracted_files = [p.name for p in root.glob("*")]
            assert "app.py" in extracted_files
            assert "app_link.py" not in extracted_files

    def test_binary_detection(self):
        """Files containing null bytes are detected as binary."""
        assert is_binary_content(b"Hello\x00World")
        assert not is_binary_content(b"Hello World\nLine 2")


# ── Noise Filtering Tests ─────────────────────────────────────────────────────

class TestNoiseFiltering:

    def test_filters_node_modules_and_git(self):
        payload = create_mock_tarball({
            "repo-main/src/index.js": "console.log('hi');\nconsole.log('bye');",
            "repo-main/node_modules/express/index.js": "module.exports = {};",
            "repo-main/.git/HEAD": "ref: refs/heads/main",
            "repo-main/dist/bundle.js": "var a=1;",
            "repo-main/package.lock": "lock data",
            "repo-main/logo.png": b"\x89PNG\r\n\x1a\n\x00\x00",
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir)
            root = unpack_tarball_safely(payload, target)
            corpus = analyze_and_build_corpus("test/repo", root)

            paths = [d.relative_path for d in corpus.documents]
            assert "src/index.js" in paths
            assert "node_modules/express/index.js" not in paths
            assert ".git/HEAD" not in paths
            assert "dist/bundle.js" not in paths
            assert "package.lock" not in paths
            assert "logo.png" not in paths


# ── Structural Analysis Tests ─────────────────────────────────────────────────

class TestStructuralAnalysis:

    def test_metrics_calculation(self):
        payload = create_mock_tarball({
            "repo-main/app.py": "import os\n\ndef main():\n    pass\n",
            "repo-main/src/utils/helper.py": "def add(a, b):\n    return a + b\n",
            "repo-main/README.md": "# Test Repo\nDescription here\n",
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir)
            root = unpack_tarball_safely(payload, target)
            corpus = analyze_and_build_corpus("test/repo", root)

            m = corpus.metrics
            assert m.file_count == 3
            assert m.total_loc == 11
            assert m.max_directory_depth == 2
            assert "Python" in m.language_breakdown
            assert "Markdown" in m.language_breakdown
            assert "README.md" in m.key_files

    def test_guaranteed_temp_directory_cleanup(self):
        """ingest_repository_archive guarantees temp directory is cleaned up."""
        payload = create_mock_tarball({"repo-main/app.py": "print('clean')"})
        corpus = ingest_repository_archive("test/clean", tar_bytes=payload)
        assert corpus.metrics.file_count == 1

        # Check that no gitnova_ingest_ directories are left in tempdir
        temp_dir = pathlib.Path(tempfile.gettempdir())
        leftovers = list(temp_dir.glob("gitnova_ingest_*"))
        assert len(leftovers) == 0


# ── Complexity Refinement Tests ───────────────────────────────────────────────

class TestComplexityRefinement:

    def test_refine_complexity_sets_structural_source(self):
        scorer = RepositoryScorer()
        prov_complexity = 50.0
        prov_signals = {
            "complexity_source": "provisional",
            "scale": 15.0,
            "backlog": 10.0,
            "community_size": 10.0,
            "onboarding_guide": -10.0,
            "doc_quality": -5.0,
        }

        refined_comp, refined_sig = scorer.refine_complexity_with_structural_metrics(
            provisional_complexity=prov_complexity,
            provisional_signals=prov_signals,
            file_count=150,
            total_loc=12000,
            max_directory_depth=4,
        )

        assert refined_sig["complexity_source"] == "structural"
        assert refined_sig["total_loc"] == 12000
        assert refined_sig["file_count"] == 150
        assert refined_sig["max_directory_depth"] == 4
        assert 0.0 <= refined_comp <= 100.0
