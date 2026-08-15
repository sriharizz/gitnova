"""
GitNova v4.2 — Repository Archive Ingestion & Security-Hardened Structural Analyzer

Responsibility:
  - Downloads lightweight repository .tar.gz archives without git history.
  - Enforces strict security safeguards for untrusted tarball payloads:
      * Download size limit (50 MB)
      * Extracted size limit (250 MB)
      * File count limit (10,000 files)
      * Single file size limit (5 MB)
      * Path Traversal Prevention (Tar-Slip protection)
      * Symlink skipping (no symlink traversal)
      * Binary detection & safe text decoding
      * Guaranteed temp directory cleanup via context management
  - Filters out vendor/build artifacts and non-code noise.
  - Extracts ground-truth structural metrics (LOC, file counts, directory depth).
  - Returns a clean, modular RepoDocumentCorpus ready for downstream processing.
"""

from dataclasses import dataclass, field
import io
import os
import pathspec
import pathlib
import shutil
import tarfile
import tempfile
from typing import Dict, List, Optional, Set, Tuple
import requests

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Security Configuration & Exceptions ──────────────────────────────────────

@dataclass
class ArchiveSecurityConfig:
    max_download_bytes: int = 50 * 1024 * 1024       # 50 MB
    max_extracted_bytes: int = 250 * 1024 * 1024     # 250 MB
    max_file_count: int = 10_000                      # 10,000 files max
    max_single_file_bytes: int = 5 * 1024 * 1024      # 5 MB per file
    download_timeout_seconds: float = 30.0            # 30s HTTP timeout


class SecurityException(Exception):
    """Base exception for archive security violations."""
    pass


class TarSlipSecurityException(SecurityException):
    """Raised when an archive member attempts directory traversal out of sandbox."""
    pass


class ArchiveLimitExceededException(SecurityException):
    """Raised when an archive exceeds file count or size limits."""
    pass


# ── Data Contracts ───────────────────────────────────────────────────────────

@dataclass
class StructuralMetrics:
    file_count: int
    directory_count: int
    max_directory_depth: int
    total_loc: int
    language_breakdown: Dict[str, int] = field(default_factory=dict)
    key_files: List[str] = field(default_factory=list)


@dataclass
class RepoDocument:
    file_path: str
    relative_path: str
    language: str
    loc: int
    size_bytes: int
    content: str


@dataclass
class RepoDocumentCorpus:
    full_name: str
    metrics: StructuralMetrics
    documents: List[RepoDocument]


# ── Extension to Language Mapping ────────────────────────────────────────────

EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".hpp": "C++ Header",
    ".cc": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".toml": "TOML",
}

IGNORED_DIR_NAMES: Set[str] = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "target",
    "out",
    ".next",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".drift",
}

IGNORED_FILE_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".exe", ".dll",
    ".so", ".dylib", ".pyc", ".pyo", ".class", ".jar", ".war",
    ".lock", ".min.js", ".min.css", ".map", ".wasm", ".db",
    ".sqlite", ".bin", ".dat", ".woof", ".woff", ".woff2", ".eot",
    ".ttf", ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".svd",  # Hardware Silicon System View Description XML assets
}


# ── Hardened Tarball Unpacker ────────────────────────────────────────────────

def is_safe_tar_member(base_dir: pathlib.Path, member: tarfile.TarInfo) -> bool:
    """
    Guarantees that extracting member will not escape base_dir (Tar-Slip protection).
    Rejects absolute paths and relative paths containing '..' escaping base_dir.
    """
    target_path = (base_dir / member.name).resolve()
    base_path = base_dir.resolve()

    try:
        # Check if base_path is a parent of target_path
        target_path.relative_to(base_path)
        return True
    except ValueError:
        return False


def is_binary_content(sample_bytes: bytes) -> bool:
    """Returns True if the sample contains null bytes (binary file signature)."""
    return b"\x00" in sample_bytes


def unpack_tarball_safely(
    tar_bytes: bytes,
    target_dir: pathlib.Path,
    security_config: ArchiveSecurityConfig = ArchiveSecurityConfig(),
) -> pathlib.Path:
    """
    Extracts a tarball into target_dir with strict security limits.
    Returns the root directory inside target_dir where code was unpacked.
    """
    if len(tar_bytes) > security_config.max_download_bytes:
        raise ArchiveLimitExceededException(
            f"Tarball payload ({len(tar_bytes)} bytes) exceeds max download limit of "
            f"{security_config.max_download_bytes} bytes"
        )

    try:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:*") as tar:
            extracted_bytes = 0
            file_count = 0

            # Inspect members before extraction
            for member in tar.getmembers():
                # 1. Path traversal check
                if not is_safe_tar_member(target_dir, member):
                    raise TarSlipSecurityException(
                        f"Malicious tar path traversal detected: {member.name}"
                    )

                # 2. Symlink/Hardlink prevention
                if member.issym() or member.islnk():
                    logger.debug("skipping_symlink", extra={"member": member.name})
                    continue

                # 3. File count check
                if member.isfile():
                    file_count += 1
                    if file_count > security_config.max_file_count:
                        raise ArchiveLimitExceededException(
                            f"Archive exceeds maximum file count limit of {security_config.max_file_count}"
                        )

                    # 4. Single file size check
                    if member.size > security_config.max_single_file_bytes:
                        logger.warning(
                            "skipping_oversized_file",
                            extra={"member": member.name, "size": member.size},
                        )
                        continue

                    extracted_bytes += member.size
                    if extracted_bytes > security_config.max_extracted_bytes:
                        raise ArchiveLimitExceededException(
                            f"Extracted payload exceeds maximum limit of {security_config.max_extracted_bytes} bytes"
                        )

                    # Extract single file safely
                    tar.extract(member, path=target_dir, numeric_owner=True)

    except (tarfile.TarError, EOFError) as e:
        raise SecurityException(f"Failed to unpack tarball payload: {str(e)}") from e

    # GitHub tarballs unpack into a single top-level root folder (e.g., owner-repo-sha)
    subdirs = [p for p in target_dir.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        return subdirs[0]
    return target_dir


# ── File Filter & Noise Removal ──────────────────────────────────────────────

class FileFilter:
    """Filters out noise, binaries, generated source code, test dataset fixtures, and build artifacts."""

    def __init__(self, root_dir: pathlib.Path):
        self.root_dir = root_dir
        self.gitignore_spec = self._load_gitignore(root_dir)

    def _load_gitignore(self, root_dir: pathlib.Path) -> Optional[pathspec.PathSpec]:
        gitignore_path = root_dir / ".gitignore"
        if not gitignore_path.is_file():
            return None
        try:
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                patterns = f.read().splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except Exception:
            return None

    def is_valid_file(self, path: pathlib.Path) -> bool:
        """Determines if a file should be included in structural analysis and corpus."""
        # 1. Must be a regular file
        if not path.is_file() or path.is_symlink():
            return False

        rel_path = path.relative_to(self.root_dir)
        rel_str = str(rel_path).replace("\\", "/")
        rel_parts = [p.lower() for p in rel_path.parts]
        filename = rel_parts[-1]

        # 2. Check directory path parts for ignored folder names
        for part in rel_parts[:-1]:
            if part in IGNORED_DIR_NAMES:
                return False

        # 3. Check file extension
        ext = path.suffix.lower()
        if ext in IGNORED_FILE_EXTENSIONS:
            return False

        # 4. Deterministic generated source code patterns
        if (
            filename.endswith(".g.dart")
            or filename.endswith(".steps.dart")
            or filename.endswith(".freezed.dart")
            or filename.endswith(".generated.dart")
            or filename.endswith(".pb.go")
            or filename.endswith("_pb2.py")
            or filename.endswith(".min.js")
            or filename.endswith(".min.css")
            or filename.endswith(".bundle.js")
        ):
            return False

        # 5. Generated schema / DB directories (e.g. test/drift/db/generated/)
        if "generated" in rel_parts[:-1] or "drift" in rel_parts[:-1]:
            if filename.startswith("schema_v") or filename.endswith(".g.dart") or filename.endswith(".steps.dart"):
                return False

        # 6. Bulk test datasets & data fixtures (path + size/LOC signal)
        if any(p in {"data", "fixtures", "testdata", "__fixtures__"} for p in rel_parts[:-1]):
            # CSV/TSV/JSON data fixtures inside test/data directories
            if ext in {".csv", ".tsv", ".json", ".txt", ".dat"}:
                # If file > 30 KB or in test data path, treat as bulk data fixture
                if path.stat().st_size > 30 * 1024 or any(p in {"test", "tests", "__tests__", "spec", "specs"} for p in rel_parts[:-1]):
                    return False

        # 7. Check .gitignore spec if available
        if self.gitignore_spec:
            try:
                if self.gitignore_spec.match_file(rel_str):
                    return False
            except Exception:
                pass

        return True


# ── Structural Analyzer & Corpus Builder ─────────────────────────────────────

def analyze_and_build_corpus(
    full_name: str,
    root_dir: pathlib.Path,
    security_config: ArchiveSecurityConfig = ArchiveSecurityConfig(),
) -> RepoDocumentCorpus:
    """
    Traverses extracted repo root_dir, computes structural metrics,
    and returns a RepoDocumentCorpus.
    """
    file_filter = FileFilter(root_dir)

    file_count = 0
    total_loc = 0
    max_depth = 0
    unique_dirs: Set[pathlib.Path] = set()
    language_breakdown: Dict[str, int] = {}
    key_files: List[str] = []
    documents: List[RepoDocument] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune ignored directory names in-place so os.walk skips descending into them
        dirnames[:] = [d for d in dirnames if d.lower() not in IGNORED_DIR_NAMES]

        current_dir = pathlib.Path(dirpath)

        for filename in filenames:
            file_path = current_dir / filename
            if not file_filter.is_valid_file(file_path):
                continue

            rel_path_obj = file_path.relative_to(root_dir)
            rel_path_str = str(rel_path_obj).replace("\\", "/")

            # Track depth & directories
            depth = len(rel_path_obj.parts) - 1
            if depth > max_depth:
                max_depth = depth
            if rel_path_obj.parent != pathlib.Path("."):
                unique_dirs.add(rel_path_obj.parent)

            # Check single file size limit
            file_size = file_path.stat().st_size
            if file_size > security_config.max_single_file_bytes:
                continue

            # Read file content safely
            try:
                with open(file_path, "rb") as f:
                    raw_bytes = f.read(1024)
                    if is_binary_content(raw_bytes):
                        continue
                    f.seek(0)
                    content_bytes = f.read()

                content = content_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                logger.debug("file_read_error", extra={"file": rel_path_str, "error": str(e)})
                continue

            # Count lines of code
            loc = content.count("\n") + (1 if content else 0)
            file_count += 1
            total_loc += loc

            # Language breakdown
            ext = file_path.suffix.lower()
            lang = EXTENSION_TO_LANGUAGE.get(ext, "Other")
            language_breakdown[lang] = language_breakdown.get(lang, 0) + loc

            # Key file identification
            upper_name = filename.upper()
            if upper_name in {
                "README", "README.MD", "README.RST", "CONTRIBUTING.MD",
                "LICENSE", "LICENSE.TXT", "PACKAGE.JSON", "PYPROJECT.TOML",
                "CARGO.TOML", "POM.XML", "BUILD.GRADLE", "GO.MOD"
            }:
                key_files.append(rel_path_str)

            documents.append(
                RepoDocument(
                    file_path=str(file_path),
                    relative_path=rel_path_str,
                    language=lang,
                    loc=loc,
                    size_bytes=file_size,
                    content=content,
                )
            )

    metrics = StructuralMetrics(
        file_count=file_count,
        directory_count=len(unique_dirs),
        max_directory_depth=max_depth,
        total_loc=total_loc,
        language_breakdown=language_breakdown,
        key_files=key_files,
    )

    return RepoDocumentCorpus(
        full_name=full_name,
        metrics=metrics,
        documents=documents,
    )


# ── Archive Downloader & High-Level Ingestion Entry Point ─────────────────────

def fetch_tarball_bytes(
    full_name: str,
    github_token: Optional[str] = None,
    security_config: ArchiveSecurityConfig = ArchiveSecurityConfig(),
) -> bytes:
    """
    Downloads repository .tar.gz archive from GitHub.
    Enforces HTTP timeout and max download size limit during streaming.
    """
    url = f"https://api.github.com/repos/{full_name}/tarball"
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=security_config.download_timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()

        downloaded_bytes = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                downloaded_bytes.extend(chunk)
                if len(downloaded_bytes) > security_config.max_download_bytes:
                    raise ArchiveLimitExceededException(
                        f"Download payload for {full_name} exceeded limit of "
                        f"{security_config.max_download_bytes} bytes"
                    )

        return bytes(downloaded_bytes)

    except requests.RequestException as e:
        raise SecurityException(f"HTTP download failed for {full_name}: {str(e)}") from e


def ingest_repository_archive(
    full_name: str,
    tar_bytes: Optional[bytes] = None,
    github_token: Optional[str] = None,
    security_config: ArchiveSecurityConfig = ArchiveSecurityConfig(),
) -> RepoDocumentCorpus:
    """
    High-level entry point for Sprint 5 Ingestion.
    Guarantees temporary workspace directory cleanup even if an exception occurs.
    """
    if tar_bytes is None:
        tar_bytes = fetch_tarball_bytes(full_name, github_token, security_config)

    temp_dir = tempfile.mkdtemp(prefix="gitnova_ingest_")
    temp_path = pathlib.Path(temp_dir)

    try:
        root_dir = unpack_tarball_safely(tar_bytes, temp_path, security_config)
        corpus = analyze_and_build_corpus(full_name, root_dir, security_config)
        logger.info(
            "repository_ingested",
            extra={
                "full_name": full_name,
                "file_count": corpus.metrics.file_count,
                "total_loc": corpus.metrics.total_loc,
                "depth": corpus.metrics.max_directory_depth,
            },
        )
        return corpus
    finally:
        # Guaranteed cleanup of temporary workspace
        shutil.rmtree(temp_dir, ignore_errors=True)
