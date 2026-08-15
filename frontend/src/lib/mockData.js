/**
 * Fallback Mock Data for GitNova v4.2 Frontend
 * Shaped 1:1 to match FastAPI Pydantic Models (IssueOut, CodeExplorerOut, StatsOut).
 * Used ONLY as a graceful fallback when local backend is unreachable.
 */

export const mockStats = {
  total_issues_analyzed: 3240,
  total_repos_qualified: 142,
  total_issues_published: 487,
  system_accuracy: 76.5,
  last_sync_at: new Date().toISOString()
};

export const mockIssues = [
  {
    id: "e4c19d4b-84a2-4a92-b43e-78149e6d0a11",
    repo_id: "a1b2c3d4-0000-0000-0000-000000000001",
    repo_full_name: "pallets/flask",
    github_issue_number: 5432,
    repo_tier: "starter",
    repo_score: 92.5,
    repo_stars: 68400,
    repo_language: "Python",
    title: "Add type hints to request module",
    ai_hint: "Add type annotations to improve type safety in Flask's request module.",
    ai_summary_preview: "The Flask request module handles incoming HTTP requests...",
    quality_score: 87,
    quality_grade: "high",
    difficulty: "BEGINNER",
    difficulty_score: 28.5,
    difficulty_tier: "BEGINNER",
    estimated_time: "~1-2 hours",
    competition_level: "low",
    freshness_label: "Updated 2 days ago",
    domain_topics: ["Web Development", "Python"],
    verification_status: "VERIFIED",
    verification_reasons: [],
    explanation: {
      status: "SUCCESS",
      summary: "The request module is missing type hints in several functions and properties. The goal is to add proper type annotations to improve type safety and developer experience.",
      why_it_happens: "Type hints help catch bugs early, improve IDE support, and make the codebase easier to maintain. This change will help contributors and users understand the code better.",
      prerequisite_concepts: [
        "Python type hints",
        "HTTP requests",
        "Flask basics",
        "PEP 484"
      ],
      step_by_step_plan: [
        {
          step_number: 1,
          title: "Read the existing Request class",
          description: "Open src/flask/wrappers.py and read lines 45-80 to understand how Request inherits from Werkzeug Wrapper.",
          target_file: "src/flask/wrappers.py"
        },
        {
          step_number: 2,
          title: "Understand current types",
          description: "Check the return types of Request.url, Request.get_data, and Request.json methods.",
          target_file: "src/flask/wrappers.py"
        },
        {
          step_number: 3,
          title: "Add the required annotations",
          description: "Add Python 3.8+ type annotations to def url(self) -> str and def get_data(self) -> bytes.",
          target_file: "src/flask/wrappers.py"
        },
        {
          step_number: 4,
          title: "Run the existing test suite",
          description: "Execute pytest tests/test_basic.py to verify that no existing functionality broke.",
          target_file: "tests/test_basic.py"
        }
      ],
      relevant_locations: [
        {
          file_path: "src/flask/wrappers.py",
          symbol_name: "Request class",
          lines: "45-80",
          role: "Primary Fix Location",
          is_verified: true
        }
      ],
      common_pitfalls: [
        "Be careful not to import heavy modules at runtime; use typing.TYPE_CHECKING if necessary."
      ],
      disclaimer: null
    },
    github_url: "https://github.com/pallets/flask/issues/5432",
    created_at: new Date().toISOString()
  },
  {
    id: "f5d20e5c-95b3-5b03-c54f-89250f7e1b22",
    repo_id: "b2c3d4e5-0000-0000-0000-000000000002",
    repo_full_name: "encode/httpx",
    github_issue_number: 1890,
    repo_tier: "starter",
    repo_score: 88.0,
    repo_stars: 23100,
    repo_language: "Python",
    title: "Improve error message for invalid URL format",
    ai_hint: "Clarify exception traceback when invalid port or path is passed to httpx.Client.",
    ai_summary_preview: "When an invalid URL format is passed, HTTPX throws an uninformative generic exception...",
    quality_score: 84,
    quality_grade: "high",
    difficulty: "BEGINNER",
    difficulty_score: 32.0,
    difficulty_tier: "BEGINNER",
    estimated_time: "~1 hour",
    competition_level: "low",
    freshness_label: "Updated 1 day ago",
    domain_topics: ["Web Development", "Python", "Networking"],
    verification_status: "VERIFIED",
    verification_reasons: [],
    explanation: {
      status: "SUCCESS",
      summary: "The error message for invalid URLs is generic. Enhance URL validation logic in httpx/_urls.py to provide specific feedback on malformed schemes or ports.",
      why_it_happens: "The URL parser catches ValueError and re-raises InvalidURL without attaching details about which part of the URL string caused parsing failure.",
      prerequisite_concepts: [
        "URL parsing RFC 3986",
        "Python Exception handling",
        "HTTPX client initialization"
      ],
      step_by_step_plan: [
        {
          step_number: 1,
          title: "Locate URL parser",
          description: "Open httpx/_urls.py and inspect the URL class __init__ method.",
          target_file: "httpx/_urls.py"
        },
        {
          step_number: 2,
          title: "Update InvalidURL exception message",
          description: "Include the invalid component in the exception string message.",
          target_file: "httpx/_urls.py"
        },
        {
          step_number: 3,
          title: "Run pytest",
          description: "Run pytest tests/test_urls.py to verify exceptions test suite.",
          target_file: "tests/test_urls.py"
        }
      ],
      relevant_locations: [
        {
          file_path: "httpx/_urls.py",
          symbol_name: "URL.__init__",
          lines: "110-145",
          role: "Validation Parser",
          is_verified: true
        }
      ],
      common_pitfalls: [
        "Do not log sensitive query parameters or authorization headers in error messages."
      ],
      disclaimer: null
    },
    github_url: "https://github.com/encode/httpx/issues/1890",
    created_at: new Date().toISOString()
  },
  {
    id: "a7e31f6d-06c4-6c14-d65a-90361a8f2c33",
    repo_id: "c3d4e5f6-0000-0000-0000-000000000003",
    repo_full_name: "scikit-learn/scikit-learn",
    github_issue_number: 24510,
    repo_tier: "established",
    repo_score: 95.0,
    repo_stars: 52400,
    repo_language: "Python",
    title: "Add docstring usage example for StandardScaler",
    ai_hint: "Expand standard scaler docstring with a clear numpy array transformation code snippet.",
    ai_summary_preview: "StandardScaler docstring lacks a simple, copy-pasteable example showing fit_transform...",
    quality_score: 90,
    quality_grade: "high",
    difficulty: "BEGINNER",
    difficulty_score: 22.0,
    difficulty_tier: "BEGINNER",
    estimated_time: "~2-3 hours",
    competition_level: "low",
    freshness_label: "Updated 5 days ago",
    domain_topics: ["Data Science", "Machine Learning", "Python"],
    verification_status: "VERIFIED",
    verification_reasons: [],
    explanation: {
      status: "SUCCESS",
      summary: "Add a simple usage example for StandardScaler in the docstring to clarify how data transformation works for newcomers.",
      why_it_happens: "Clear docstring examples reduce friction for beginners trying scikit-learn preprocessing classes.",
      prerequisite_concepts: [
        "NumPy array structure",
        "Docstring Examples / doctest format",
        "Scikit-learn Transformer API"
      ],
      step_by_step_plan: [
        {
          step_number: 1,
          title: "Open StandardScaler file",
          description: "Navigate to sklearn/preprocessing/_data.py and find class StandardScaler.",
          target_file: "sklearn/preprocessing/_data.py"
        },
        {
          step_number: 2,
          title: "Add >>> doctest block",
          description: "Add a 4-line Example block showing fit_transform on a 2x2 matrix.",
          target_file: "sklearn/preprocessing/_data.py"
        },
        {
          step_number: 3,
          title: "Verify doctest",
          description: "Run pytest sklearn/preprocessing/_data.py to ensure doctests pass.",
          target_file: "sklearn/preprocessing/_data.py"
        }
      ],
      relevant_locations: [
        {
          file_path: "sklearn/preprocessing/_data.py",
          symbol_name: "StandardScaler",
          lines: "620-675",
          role: "Docstring target",
          is_verified: true
        }
      ],
      common_pitfalls: [
        "Ensure floating point outputs match the exact doctest formatting."
      ],
      disclaimer: null
    },
    github_url: "https://github.com/scikit-learn/scikit-learn/issues/24510",
    created_at: new Date().toISOString()
  }
];

export const mockRecommendations = {
  issues: mockIssues,
  total_count: mockIssues.length,
  filters_applied: {
    languages: ["Python"],
    domains: ["Web Development", "Data Science"],
    difficulty: "BEGINNER"
  }
};

export const mockIssueCode = (issueId) => {
  const issue = mockIssues.find(i => i.id === issueId) || mockIssues[0];
  return {
    issue_id: issue.id,
    repo_full_name: issue.repo_full_name,
    commit_sha: "ea960d37b7a6c6a032ba9f72e41ed0d1c0078f9e",
    files: [
      {
        file_path: "src/flask/wrappers.py",
        role: "Primary Target",
        symbol_name: "Request",
        start_line: 45,
        end_line: 80,
        content: `class Request(WerkzeugRequest):\n    """The request object used by default in Flask."""\n\n    def __init__(self, environ: dict) -> None:\n        super().__init__(environ)\n\n    @property\n    def url(self) -> str:\n        """The full request URL including query parameters."""\n        return self.environ.get("REQUEST_URI", "")\n\n    def get_data(self, cache: bool = True) -> bytes:\n        """Read and return binary request body payload."""\n        return super().get_data(cache=cache)\n\n    def json(self) -> dict:\n        """Parse incoming request body as JSON."""\n        return self.get_json()`,
        language: "python",
        is_verified: true,
        github_file_url: `https://github.com/${issue.repo_full_name}/blob/main/src/flask/wrappers.py#L45-L80`
      },
      {
        file_path: "src/flask/app.py",
        role: "Caller Context",
        symbol_name: "Flask.make_request",
        start_line: 120,
        end_line: 145,
        content: `def make_request(self, environ: dict) -> Request:\n    """Creates a Request object for the current WSGI environment."""\n    return self.request_class(environ)`,
        language: "python",
        is_verified: true,
        github_file_url: `https://github.com/${issue.repo_full_name}/blob/main/src/flask/app.py#L120-L145`
      }
    ]
  };
};
