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
    def test_rejects_proposal_title(self):
        result = pre_filter_issue("Proposal: Rewrite the rendering engine", "This is a detailed body with enough words to pass the minimum word count threshold easily")
        assert result['pass'] is False
        assert "Proposal" in result['reason'] or "proposal" in result['reason']

    def test_rejects_rfc_title(self):
        result = pre_filter_issue("RFC: Parameter Server Training for Keras JAX backend", "A detailed proposal for implementing parameter server training with many words here")
        assert result['pass'] is False

    def test_rejects_roadmap_title(self):
        result = pre_filter_issue("[Roadmap] DeepSpeed Q1 2026", "Here is our roadmap for the first quarter with all planned items and milestones listed")
        assert result['pass'] is False

    def test_rejects_short_body(self):
        result = pre_filter_issue("Fix button color", "Just fix it please")
        assert result['pass'] is False
        assert "too short" in result['reason'].lower()

    def test_rejects_allcaps_title(self):
        result = pre_filter_issue("FIX THIS NOW BROKEN URGENT ASAP", "This is a detailed body with plenty of words describing the actual bug in question and what happened")
        assert result['pass'] is False
        assert "uppercase" in result['reason'].lower()

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
        assert "checklist" in result['reason'].lower() or "epic" in result['reason'].lower()

    def test_rejects_non_code_labels(self):
        result = pre_filter_issue("How to configure logging?", "I want to know how to configure logging in this project because I cannot find any documentation about it and its confusing",
                                  labels=[{"name": "question"}])
        assert result['pass'] is False

    def test_passes_good_issue(self):
        result = pre_filter_issue(
            "Button onClick handler fires twice on mobile Safari",
            "When tapping a button on iOS Safari, the onClick handler fires twice. "
            "This happens specifically on the submit button in the checkout flow. "
            "Steps to reproduce: 1. Open checkout page on iPhone. 2. Tap submit. "
            "3. Observe two network requests being sent. Expected: One request."
        )
        assert result['pass'] is True

    def test_passes_normal_bug(self):
        result = pre_filter_issue(
            "TypeError in date formatting function",
            "Getting a TypeError when passing an ISO string to formatDate(). "
            "Stack trace shows it breaks in src/utils/date.ts at line 42. "
            "The function receives undefined instead of a Date object when "
            "the input string has no timezone offset."
        )
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
