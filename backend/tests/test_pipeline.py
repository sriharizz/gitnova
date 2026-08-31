"""
GitNova Pipeline Unit Tests
============================
Tests for all new pipeline modules:
- pre_filter
- post_validator
- quality_scorer
- repo_grounding (mocked)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.pipeline.pre_filter import pre_filter_issue, pre_filter_issue_from_csv
from app.pipeline.post_validator import validate_llama_output, validate_hint_from_csv
from app.pipeline.quality_scorer import compute_quality_score


# ═══════════════════════════════════════════
# PRE-FILTER TESTS
# ═══════════════════════════════════════════

class TestPreFilter:
    # 1. Valid English bug
    def test_passes_valid_english_bug(self):
        result = pre_filter_issue(
            "TypeError in date formatting function",
            "Getting a TypeError when passing an ISO string to formatDate(). "
            "Stack trace shows it breaks in src/utils/date.ts at line 42. "
            "The function receives undefined instead of a Date object when "
            "the input string has no timezone offset."
        )
        assert result['pass'] is True
        assert result['eligible'] is True

    # 2. Valid English feature
    def test_passes_valid_english_feature(self):
        result = pre_filter_issue(
            "Add support for custom headers in HTTP client",
            "We should allow users to configure custom default headers when initializing "
            "the ApiClient instance. This is useful for passing authentication tokens "
            "and custom User-Agent headers across all outgoing requests."
        )
        assert result['pass'] is True

    # 3. Valid documentation issue
    def test_passes_valid_documentation_issue(self):
        result = pre_filter_issue(
            "Fix typo in README installation instructions",
            "The README currently instructs users to run `npm install --save react-router` "
            "instead of `npm install react-router-dom`. We should update this to prevent confusion.",
            labels=[{"name": "documentation"}]
        )
        assert result['pass'] is True

    # 4. Valid question / actionable discussion
    def test_passes_valid_question_or_discussion(self):
        result = pre_filter_issue(
            "How to configure logging format in config.yaml?",
            "I want to know how to configure structured JSON logging in this project because "
            "the standard logging output is plain text and our log aggregator requires JSON timestamps."
        )
        assert result['pass'] is True

    # 5. Empty title -> FAIL
    def test_rejects_empty_title(self):
        result = pre_filter_issue("", "This is a body with plenty of words describing a problem.")
        assert result['pass'] is False
        assert result['rule_id'] == "EMPTY_TITLE"
        assert "EMPTY_TITLE" in result['reason_codes']

    # 6. Empty / near-empty body -> FAIL
    def test_rejects_empty_or_near_empty_body(self):
        result = pre_filter_issue("Fix button color", "Just fix it")
        assert result['pass'] is False
        assert result['rule_id'] == "EMPTY_BODY"

    # 7. Pull request record -> FAIL
    def test_rejects_pull_request_record(self):
        result = pre_filter_issue(
            "Fix navbar responsive breakpoint",
            "This pull request updates the CSS media queries for tablet devices.",
            is_pr=True,
            html_url="https://github.com/org/repo/pull/123"
        )
        assert result['pass'] is False
        assert result['rule_id'] == "PULL_REQUEST"

    # 8. Closed issue -> FAIL
    def test_rejects_closed_issue(self):
        result = pre_filter_issue(
            "Memory leak in worker connection pool",
            "Workers do not release TCP connections after timeout occurs in production.",
            state="closed"
        )
        assert result['pass'] is False
        assert result['rule_id'] == "CLOSED_ISSUE"

    # 9. Obvious Chinese content -> FAIL for English primary feed
    def test_rejects_obvious_chinese_content(self):
        result = pre_filter_issue(
            "启动服务时数据库连接失败",
            "在Windows环境下运行npm start时，程序无法连接到本地PostgreSQL数据库，报错提示连接超时，请问如何解决？"
        )
        assert result['pass'] is False
        assert result['rule_id'] == "NON_ENGLISH_CONTENT"

    # 10. Obvious Cyrillic content -> FAIL for English primary feed
    def test_rejects_obvious_cyrillic_content(self):
        result = pre_filter_issue(
            "Ошибка при инициализации модуля конфигурации",
            "При запуске приложения возникает исключение FileNotFoundException в модуле загрузки настроек."
        )
        assert result['pass'] is False
        assert result['rule_id'] == "NON_ENGLISH_CONTENT"

    # 11. English issue containing code and URLs -> PASS
    def test_passes_english_issue_with_code_and_urls(self):
        body = (
            "When sending a request to https://api.example.com/v1/users with the following payload:\n"
            "```json\n"
            "{\"user_id\": \"usr_12345\", \"status\": \"ACTIVE\"}\n"
            "```\n"
            "The client throws a ValidationError at `src/client.py` line 88. "
            "Please see documentation at https://docs.example.com/errors for expected behavior."
        )
        result = pre_filter_issue("Validation error when creating user via API endpoint", body)
        assert result['pass'] is True

    # 12. Stack trace-heavy English issue -> PASS
    def test_passes_stack_trace_heavy_english_issue(self):
        body = (
            "The application crashed on startup with this stack trace:\n"
            "```\n"
            "Traceback (most recent call last):\n"
            "  File \"app/main.py\", line 14, in <module>\n"
            "    from app.db.connection import init_db\n"
            "  File \"app/db/connection.py\", line 28, in init_db\n"
            "    raise ConnectionError(\"Failed to connect to host\")\n"
            "ConnectionError: Failed to connect to host\n"
            "```\n"
            "This happens whenever the DATABASE_URL environment variable is unset."
        )
        result = pre_filter_issue("Crash with ConnectionError when DATABASE_URL is missing", body)
        assert result['pass'] is True

    # 13. Technical identifiers and abbreviations -> PASS
    def test_passes_technical_identifiers_and_abbreviations(self):
        result = pre_filter_issue(
            "NullPointerException in KafkaConsumerConfigProvider when SSL_ENABLED is true",
            "When deploying to AWS EKS with IAM_ROLE authentication, the getKafkaConfig() method "
            "throws an NPE. The sslKeyStorePassword property is evaluated before initialization."
        )
        assert result['pass'] is True

    # 14. Borderline multilingual issue (foreign proper names) -> PASS
    def test_passes_borderline_multilingual_with_foreign_author_or_word(self):
        result = pre_filter_issue(
            "Fix localization crash reported by François for Tokyo server",
            "Users in the São Paulo and München offices report that currency formatting fails "
            "when switching locales. The formatCurrency() function needs to handle multi-byte symbols properly."
        )
        assert result['pass'] is True

    # 15. Bot / System generated content -> FAIL
    def test_rejects_bot_or_system_generated_content(self):
        result_bot = pre_filter_issue(
            "Bump certifi from 2024.2.2 to 2024.7.4",
            "Bumps certifi from 2024.2.2 to 2024.7.4. Release notes and changelog are available in the repository.",
            author="dependabot[bot]"
        )
        assert result_bot['pass'] is False
        assert result_bot['rule_id'] == "BOT_OR_SYSTEM_CONTENT"

        result_stale = pre_filter_issue(
            "This issue has been automatically marked as stale",
            "This issue has been automatically marked as stale because it has not had recent activity.",
            author="stale[bot]"
        )
        assert result_stale['pass'] is False
        assert result_stale['rule_id'] == "BOT_OR_SYSTEM_CONTENT"

    # Legacy Noise & Screaming tests
    def test_rejects_allcaps_title(self):
        result = pre_filter_issue("FIX THIS NOW BROKEN URGENT ASAP", "This is a detailed body with plenty of words describing the actual bug in question and what happened")
        assert result['pass'] is False
        assert result['rule_id'] == "ALL_CAPS_TITLE"

    def test_rejects_epic_with_checklists(self):
        body = """Tracking issue for the v2 release:
        - [ ] Port auth module
        - [ ] Port database layer
        - [ ] Change API endpoints
        - [ ] Port frontend components
        - [ ] Add integration tests
        - [ ] Deploy to staging
        """
        result = pre_filter_issue("v2 Release Tracking", body)
        assert result['pass'] is False
        assert result['rule_id'] == "EPIC_TRACKING_ISSUE"


class TestRantToneHardening:
    # 1. iss != sub -> PASS
    def test_passes_jwt_assertion_with_inequality(self):
        body = (
            "When authenticating via JWT-profile assertion, the server returns 400 Bad Request "
            "whenever `iss != sub`. In our enterprise multi-tenant configuration, the issuer ID "
            "and subject ID represent distinct entities according to RFC 7523 section 3. "
            "We need to allow `iss != sub` when client_assertion_type is configured."
        )
        result = pre_filter_issue("[Bug]: JWT-profile assertion with iss != sub returns 400", body)
        assert result['pass'] is True

    # 2. x == y -> PASS
    def test_passes_equality_operator(self):
        body = (
            "The comparison function in `src/matcher.py` fails when evaluating if `x == y`. "
            "Because `x` is a floating point numpy array and `y` is a scalar, the operator returns "
            "a boolean array instead of a single truth value, causing ValueError: The truth value of an array is ambiguous."
        )
        result = pre_filter_issue("Comparison error when x == y in matcher module", body)
        assert result['pass'] is True

    # 3. x <= y -> PASS
    def test_passes_comparison_operator(self):
        body = (
            "In the rate limiter algorithm, we should verify that `x <= y` before resetting the token bucket. "
            "Currently, if `x > y` the remaining tokens become negative, leading to unexpected 429 errors for legitimate clients."
        )
        result = pre_filter_issue("Rate limiter token underflow when x <= y condition fails", body)
        assert result['pass'] is True

    # 4. #!/bin/bash -> PASS
    def test_passes_shell_shebang(self):
        body = (
            "The bootstrap script fails on Ubuntu 24.04 LTS:\n"
            "```bash\n"
            "#!/bin/bash\n"
            "set -euo pipefail\n"
            "docker-verify.sh exits 1 with no message\n"
            "```\n"
            "When running in non-interactive CI environments, the docker verification script terminates unexpectedly."
        )
        result = pre_filter_issue("docker-verify.sh exits 1 with no message on clean checkout", body)
        assert result['pass'] is True

    # 5. Markdown screenshot syntax -> PASS
    def test_passes_markdown_screenshot_syntax(self):
        body = (
            "The dark mode toggle has visual artifacts across the header bar.\n\n"
            "![screenshot 1](https://example.com/assets/screen1.png)\n"
            "![screenshot 2](https://example.com/assets/screen2.png)\n"
            "![screenshot 3](https://example.com/assets/screen3.png)\n\n"
            "Notice how the border radius clips the user profile avatar in the navigation component."
        )
        result = pre_filter_issue("Dark mode toggle navigation bar visual clipping", body)
        assert result['pass'] is True

    # 6. Code containing ! -> PASS
    def test_passes_code_containing_exclamation(self):
        body = (
            "When checking validation state in `src/validator.ts`, the condition `if (!isValid || !isReady)` "
            "evaluates incorrectly because `isValid` is undefined during initial mount. "
            "In Rust bindings, `println!(\"error occurred!\")` also causes a panic on unwrap."
        )
        result = pre_filter_issue("Uncaught TypeError during validation condition check", body)
        assert result['pass'] is True

    # 7. URL containing punctuation -> PASS
    def test_passes_url_containing_punctuation(self):
        body = (
            "The query parser fails when parsing incoming webhook URLs containing exclamation marks: "
            "https://api.example.com/v1/events?filter=critical!&tag=release-v2.0! "
            "The percent-encoding logic strips the exclamation mark and corrupts the HMAC signature."
        )
        result = pre_filter_issue("HMAC verification fails on query parameters with special characters", body)
        assert result['pass'] is True

    # 8. Stack trace with punctuation -> PASS
    def test_passes_stack_trace_with_punctuation(self):
        body = (
            "Encountered unhandled exception during database connection initialization:\n"
            "```\n"
            "Traceback (most recent call last):\n"
            "  File \"src/db.py\", line 45, in connect\n"
            "    raise RuntimeError(\"FATAL: Database host unreachable! Connection refused!\")\n"
            "RuntimeError: FATAL: Database host unreachable! Connection refused!\n"
            "```\n"
            "This occurs whenever the primary node fails over to the replica."
        )
        result = pre_filter_issue("Database failover crashes with unhandled RuntimeError", body)
        assert result['pass'] is True

    # 9. Technical issue with many code symbols and acronyms -> PASS
    def test_passes_technical_issue_with_many_code_symbols(self):
        body = (
            "When sending HTTP POST requests with Content-Type: application/json to AWS API Gateway, "
            "the JWT authorization header fails validation if `iss != sub` or `exp <= iat`. "
            "The CLI response code is HTTP 401 UNAUTHORIZED with JSON payload error details."
        )
        result = pre_filter_issue("HTTP 401 on AWS API Gateway JWT authorization validation", body)
        assert result['pass'] is True

    # 10. Genuine emotional rant prose -> REJECT
    def test_rejects_genuine_screaming_rant_prose(self):
        body = (
            "THIS IS COMPLETELY BROKEN!!! WHY DOES THIS KEEP HAPPENING!!!! "
            "PLEASE FIX THIS STUPID SYSTEM IMMEDIATELY THIS IS UNUSABLE AND TERRIBLE!!!!"
        )
        result = pre_filter_issue("SYSTEM COMPLETELY BROKEN FIX NOW", body)
        assert result['pass'] is False
        assert result['rule_id'] in ["RANT_TONE", "ALL_CAPS_TITLE"]

    # 11. Mixed technical issue + mild single exclamation -> PASS
    def test_passes_mixed_technical_issue_with_mild_single_exclamation(self):
        body = (
            "When running `npm test`, the Jest test runner times out after 5000ms on the auth test suite. "
            "This happens because the mock Redis server does not start in time. Please help take a look! "
            "Steps to reproduce: 1. Clone repository 2. Run npm install 3. Run npm test."
        )
        result = pre_filter_issue("Jest auth test suite times out on CI runners", body)
        assert result['pass'] is True

    # 12. Borderline technical case -> PASS
    def test_passes_borderline_technical_case(self):
        body = (
            "Summary of problem: The HTTP REST API client throws a NullPointerException in EKS cluster. "
            "Here is the curl command: `curl -X POST https://api.prod.local/v1/auth -H 'Content-Type: application/json'`\n"
            "Notice that `iss != sub` and `response_status != 200`!\n"
            "![diagram](https://example.com/arch.png)\n"
            "We should update the default configuration to handle this cleanly."
        )
        result = pre_filter_issue("NullPointerException during auth token refresh in EKS", body)
        assert result['pass'] is True


class TestPreFilterCSV:
    def test_rejects_roadmap_in_csv(self):
        result = pre_filter_issue_from_csv("[Roadmap] DeepSpeed Roadmap Q1 2026", "some hint")
        assert result['pass'] is False

    def test_passes_normal_title_in_csv(self):
        result = pre_filter_issue_from_csv("Fix date formatting bug in locale module", "some hint")
        assert result['pass'] is True


# ═══════════════════════════════════════════
# POST-VALIDATOR TESTS
# ═══════════════════════════════════════════

class TestPostValidator:
    def setup_method(self):
        self.java_context = {
            "language": "Java",
            "language_lower": "java",
            "valid_extensions": [".java"],
            "top_dirs": ["src/", "lib/", "test/"],
        }
        self.python_context = {
            "language": "Python",
            "language_lower": "python",
            "valid_extensions": [".py"],
            "top_dirs": ["torch/", "test/", "tools/"],
        }

    def test_catches_wrong_extension(self):
        hint = """**🎯 Goal:** Fix rendering
        
**📂 Files:**
- `src/components/Button.tsx`
- `src/utils/render.ts`

**🔧 Change:**
1. In `ButtonRenderer.handleClick()`, add debounce logic
2. Insert a 300ms delay using `setTimeout()`"""
        passed, failures = validate_llama_output(hint, "Java")
        assert passed is False
        assert any("extension" in f.lower() for f in failures)

    def test_catches_boilerplate(self):
        hint = """**🎯 Goal:** Fix the issue

**📂 Files:**
- `src/main/java/App.java`

**🔧 Change:**
1. Review the existing implementation to understand the logic.
2. Investigate the root cause of the bug.
3. Update the code to fix the issue. Test the changes thoroughly."""
        passed, failures = validate_llama_output(hint, "Java")
        assert passed is False
        assert any("boilerplate" in f.lower() for f in failures)

    def test_passes_good_hint(self):
        hint = """**🎯 Goal:** Add null safety to UserService

**📂 Files:**
- `src/main/java/com/app/UserService.java`
- `src/main/java/com/app/UserRepository.java`

**🔧 Change:**
1. In `UserService.findById()`, add explicit validation before calling `UserRepository.get(id)`
2. Replace the raw return with `Optional.ofNullable()` wrapper
3. In `UserController.getUser()`, handle the empty Optional by returning a 404 response"""
        passed, failures = validate_llama_output(hint, "Java")
        assert passed is True
        assert len(failures) == 0

    def test_catches_python_in_java_repo(self):
        hint = """**📂 Files:**
- `src/utils/helper.ts`

**🔧 Change:**
1. In `HelperClass.process()`, add validation for the input parameter"""
        passed, failures = validate_llama_output(hint, "Java")
        assert passed is False
        assert any("hallucination" in f.lower() for f in failures)


# ═══════════════════════════════════════════
# QUALITY SCORER TESTS
# ═══════════════════════════════════════════

class TestQualityScorer:
    def setup_method(self):
        self.python_context = {
            "language": "Python",
            "language_lower": "python",
            "valid_extensions": [".py"],
            "top_dirs": ["torch/", "test/", "tools/", "aten/", "c10/"],
            "topics": ["deep-learning", "python", "pytorch"],
        }

    def test_high_quality_score(self):
        hint = """**🎯 Goal:** Add LayerNorm fusion for CUDA backend

**📂 Files:**
- `torch/nn/modules/normalization.py`
- `aten/src/ATen/native/layer_norm.cpp`
- `torch/csrc/jit/passes/fuse_linear.py`

**🔧 Change:**
1. In `LayerNorm.forward()`, add a fast-path check using `torch._C._jit_pass_fuse_layer_norm()`
2. In `layer_norm.cpp`, add a CUDA kernel registration via `REGISTER_DISPATCH(layer_norm_stub, &layer_norm_kernel)`
3. In `FuseLinear.run()`, insert a new pattern match for consecutive LayerNorm + Linear pairs"""
        
        score = compute_quality_score(hint, self.python_context)
        assert score['grade'] == 'High'
        assert score['overall'] >= 70

    def test_low_quality_score(self):
        hint = """Fix the bug and make it work properly."""
        
        score = compute_quality_score(hint, self.python_context)
        assert score['grade'] == 'Low'
        assert score['overall'] < 40

    def test_medium_quality_score(self):
        hint = """**🎯 Goal:** Add caching to data loader

**📂 Files:**
- `src/components/DataLoader.tsx`

**🔧 Change:**
1. Add a cache dictionary to store loaded results
2. Check cache before making network request"""
        
        score = compute_quality_score(hint, self.python_context)
        # .tsx in a Python repo should hurt alignment, but has some structure
        assert score['grade'] in ['Low', 'Medium']

    def test_empty_hint_scores_zero(self):
        score = compute_quality_score("", self.python_context)
        assert score['overall'] == 0
        assert score['grade'] == 'Low'


# ═══════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
