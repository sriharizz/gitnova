"""
Unit tests for GitNova v4.2 FileFilter noise & generated content detection.
"""

import pathlib
import tempfile
import pytest

from app.intelligence.ingestor import FileFilter, IGNORED_FILE_EXTENSIONS, IGNORED_DIR_NAMES


def test_file_filter_valid_source_files(tmp_path):
    filter_engine = FileFilter(tmp_path)

    # Valid source files
    py_file = tmp_path / "app" / "main.py"
    py_file.parent.mkdir(parents=True, exist_ok=True)
    py_file.write_text("print('hello')", encoding="utf-8")

    ts_file = tmp_path / "src" / "index.ts"
    ts_file.parent.mkdir(parents=True, exist_ok=True)
    ts_file.write_text("console.log('hi');", encoding="utf-8")

    go_file = tmp_path / "cmd" / "main.go"
    go_file.parent.mkdir(parents=True, exist_ok=True)
    go_file.write_text("package main", encoding="utf-8")

    assert filter_engine.is_valid_file(py_file) is True
    assert filter_engine.is_valid_file(ts_file) is True
    assert filter_engine.is_valid_file(go_file) is True


def test_file_filter_legitimate_tests_and_docs(tmp_path):
    filter_engine = FileFilter(tmp_path)

    # Valid unit tests
    test_py = tmp_path / "tests" / "test_main.py"
    test_py.parent.mkdir(parents=True, exist_ok=True)
    test_py.write_text("def test_foo(): assert True", encoding="utf-8")

    test_go = tmp_path / "pkg" / "util_test.go"
    test_go.parent.mkdir(parents=True, exist_ok=True)
    test_go.write_text("func TestUtil(t *testing.T) {}", encoding="utf-8")

    # Valid documentation and config
    readme = tmp_path / "README.md"
    readme.write_text("# Project", encoding="utf-8")

    contrib = tmp_path / "CONTRIBUTING.md"
    contrib.write_text("# Contributing", encoding="utf-8")

    config = tmp_path / "pyproject.toml"
    config.write_text("[tool.poetry]", encoding="utf-8")

    assert filter_engine.is_valid_file(test_py) is True
    assert filter_engine.is_valid_file(test_go) is True
    assert filter_engine.is_valid_file(readme) is True
    assert filter_engine.is_valid_file(contrib) is True
    assert filter_engine.is_valid_file(config) is True


def test_file_filter_generated_files_and_noise(tmp_path):
    filter_engine = FileFilter(tmp_path)

    # Generated Dart code
    g_dart = tmp_path / "lib" / "model.g.dart"
    g_dart.parent.mkdir(parents=True, exist_ok=True)
    g_dart.write_text("// GENERATED CODE", encoding="utf-8")

    steps_dart = tmp_path / "lib" / "database.steps.dart"
    steps_dart.write_text("// GENERATED STEPS", encoding="utf-8")

    # Minified assets
    min_js = tmp_path / "dist" / "app.min.js"
    min_js.parent.mkdir(parents=True, exist_ok=True)
    min_js.write_text("var a=1;", encoding="utf-8")

    # Hardware Silicon System View Description (.svd)
    svd_file = tmp_path / "svd" / "esp32.svd"
    svd_file.parent.mkdir(parents=True, exist_ok=True)
    svd_file.write_text("<device></device>", encoding="utf-8")

    assert filter_engine.is_valid_file(g_dart) is False
    assert filter_engine.is_valid_file(steps_dart) is False
    assert filter_engine.is_valid_file(min_js) is False
    assert filter_engine.is_valid_file(svd_file) is False


def test_file_filter_bulk_test_datasets(tmp_path):
    filter_engine = FileFilter(tmp_path)

    # Large test dataset CSV file (>30 KB)
    large_csv = tmp_path / "tests" / "data" / "slippage.csv"
    large_csv.parent.mkdir(parents=True, exist_ok=True)
    large_csv.write_bytes(b"col1,col2\n" + b"1,2\n" * 2000)

    # Small legitimate CSV file
    small_csv = tmp_path / "config" / "settings.csv"
    small_csv.parent.mkdir(parents=True, exist_ok=True)
    small_csv.write_text("key,value\na,1", encoding="utf-8")

    assert filter_engine.is_valid_file(large_csv) is False
    assert filter_engine.is_valid_file(small_csv) is True
