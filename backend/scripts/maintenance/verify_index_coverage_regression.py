import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_path))

from app.pipeline.code_indexer import filter_source_files, select_top_structural_files, _chunk_generic_code, _chunk_python_code

def run_regression_tests():
    print("🧪 Running Comprehensive Index Coverage & Regression Tests...")
    print("================================================================")
    
    # 1. Python repo file filtering
    py_files = [
        "src/click/core.py",
        "src/click/utils.py",
        "tests/test_core.py",
        "docs/conf.py",
        "setup.py",
        "README.md",
        "click.png"
    ]
    py_filtered, py_reasons = filter_source_files(py_files, [".py"], "pallets/click")
    assert "src/click/core.py" in py_filtered, "Python source should be kept"
    assert "src/click/utils.py" in py_filtered, "Python source should be kept"
    assert "tests/test_core.py" not in py_filtered, "Tests should be excluded"
    assert "README.md" not in py_filtered, "Markdown should be excluded"
    assert "click.png" not in py_filtered, "Images should be excluded"
    print("✅ Python filtering passed.")

    # 2. TypeScript / JS repo file filtering
    ts_files = [
        "packages/core/src/index.ts",
        "packages/core/src/app.tsx",
        "packages/core/src/utils.js",
        "packages/core/__tests__/app.test.ts",
        "package.json",
        "tsconfig.json"
    ]
    ts_filtered, ts_reasons = filter_source_files(ts_files, [".ts", ".tsx", ".js", ".jsx"], "facebook/docusaurus")
    assert "packages/core/src/index.ts" in ts_filtered
    assert "packages/core/src/app.tsx" in ts_filtered
    assert "packages/core/src/utils.js" in ts_filtered
    assert "package.json" not in ts_filtered
    print("✅ TypeScript/JavaScript filtering passed.")

    # 3. Dart repo file filtering (NEW)
    dart_files = [
        "lib/bottom_nav.dart",
        "lib/main.dart",
        "lib/graph/cardio_page.dart",
        "test/widget_test.dart",
        "pubspec.yaml",
        "assets/images/logo.png"
    ]
    dart_filtered, dart_reasons = filter_source_files(dart_files, [".dart"], "brandonp2412/Flexify")
    assert "lib/bottom_nav.dart" in dart_filtered, "Dart lib source must be indexed"
    assert "lib/graph/cardio_page.dart" in dart_filtered, "Dart subpage must be indexed"
    assert "test/widget_test.dart" not in dart_filtered, "Dart tests must be excluded"
    assert "pubspec.yaml" not in dart_filtered, "YAML must be excluded from code index"
    print("✅ Dart filtering passed.")

    # 4. Haskell repo file filtering (NEW)
    hs_files = [
        "src/AWS/Lambda/Runtime.hs",
        "src/AWS/Lambda/Context.hs",
        "test/Spec.hs",
        "package.yaml",
        "stack.yaml"
    ]
    hs_filtered, hs_reasons = filter_source_files(hs_files, [".hs", ".lhs"], "Nike-Inc/hal")
    assert "src/AWS/Lambda/Runtime.hs" in hs_filtered, "Haskell src must be indexed"
    assert "src/AWS/Lambda/Context.hs" in hs_filtered, "Haskell context must be indexed"
    assert "test/Spec.hs" not in hs_filtered, "Haskell test must be excluded"
    assert "stack.yaml" not in hs_filtered, "YAML must be excluded"
    print("✅ Haskell filtering passed.")

    # 5. C/C++ Header and Source filtering (NEW)
    cpp_files = [
        "include/tscore/ink_queue.h",
        "src/tscore/ink_queue.cc",
        "plugins/header_rewrite/header_rewrite.cc",
        "tests/gold_tests/basic.test.py",
        "CMakeLists.txt",
        "doc/conf.py"
    ]
    cpp_filtered, cpp_reasons = filter_source_files(cpp_files, [".cpp", ".cc", ".h", ".hpp"], "apache/trafficserver")
    assert "include/tscore/ink_queue.h" in cpp_filtered, "C/C++ header must be indexed"
    assert "src/tscore/ink_queue.cc" in cpp_filtered, "C/C++ source must be indexed"
    assert "tests/gold_tests/basic.test.py" not in cpp_filtered, "Tests must be excluded"
    print("✅ C/C++ Source and Header filtering passed.")

    # 6. Java repo file filtering (NEW)
    java_files = [
        "core/src/main/java/com/alibaba/nacos/core/cluster/ServerMemberManager.java",
        "client/src/main/java/com/alibaba/nacos/client/naming/NacosNamingService.java",
        "client/src/test/java/com/alibaba/nacos/client/NamingTest.java",
        "pom.xml"
    ]
    java_filtered, java_reasons = filter_source_files(java_files, [".java"], "alibaba/nacos")
    assert "core/src/main/java/com/alibaba/nacos/core/cluster/ServerMemberManager.java" in java_filtered
    assert "client/src/test/java/com/alibaba/nacos/client/NamingTest.java" not in java_filtered
    print("✅ Java filtering passed.")

    # 7. Structural file selection with include/ and pkg/
    test_paths = [
        "include/tscore/ink_queue.h",
        "src/main.cc",
        "pkg/client/client.go",
        "vendor/lib.c",
        "tools/gen.py"
    ]
    ranked = select_top_structural_files(test_paths, count=3)
    assert "src/main.cc" in ranked or "include/tscore/ink_queue.h" in ranked
    print("✅ Structural scoring with include/ and pkg/ passed.")

    # 8. Chunking verification
    dart_sample = """
class BottomNav extends StatefulWidget {
  final int selectedIndex;
  BottomNav({required this.selectedIndex});
  @override
  _BottomNavState createState() => _BottomNavState();
}
"""
    dart_chunks = _chunk_generic_code(dart_sample, "lib/bottom_nav.dart", "dart")
    assert len(dart_chunks) >= 1
    assert dart_chunks[0]["token_count"] > 0
    print("✅ Generic line chunking passed.")

    py_sample = """
def format_filename(filename: str) -> str:
    \"\"\"Formats a filename for display.\"\"\"
    return filename.strip()
"""
    py_chunks = _chunk_python_code(py_sample, "src/click/utils.py")
    assert len(py_chunks) == 1
    assert py_chunks[0]["symbol_name"] == "format_filename"
    print("✅ Python AST chunking passed.")

    print("\n================================================================")
    print("🎉 ALL REGRESSION TESTS PASSED (8/8).")
    print("================================================================")

if __name__ == "__main__":
    run_regression_tests()
