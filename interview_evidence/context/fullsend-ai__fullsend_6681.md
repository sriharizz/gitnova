# Issue Context Dossier: `fullsend-ai/fullsend` #6681

**Title:** Dynamically inject harness-listed skills into agent prompt frontmatter for always-on activation  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Skills declared in a harness configuration's `skills:` list are uploaded to the sandbox and listed at runtime, but models frequently fail to invoke them via the Skill tool. The feature request proposes dynamically injecting these harness-listed skill names into the agent prompt's YAML frontmatter `skills:` section at runtime to guarantee always-on activation.

## 2. Root Cause Analysis
> Agent prompt definitions (such as markdown files with YAML frontmatter like `agents/triage.md`) declare active skills in their frontmatter. When harness files specify custom skills, the runtime loads them into the sandbox environment but does not bridge the harness skill declarations into the agent prompt's frontmatter, causing the model to miss them.

## 3. Grounded Code Locations & Citations
- File: `internal/fetchsvc/service.go` (Lines: `36-75`) | Symbol: `Service` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect harness skill loading and agent prompt construction**: Examine internal/fetchsvc/service.go to locate where harness configurations and skill lists are retrieved, and how agent prompts with YAML frontmatter are constructed. (Target: `internal/fetchsvc/service.go`)
2. **Implement dynamic skill injection into prompt frontmatter**: Modify the service logic in internal/fetchsvc/service.go so that skills declared in the harness configuration's `skills:` list are dynamically injected into the agent prompt's YAML frontmatter `skills:` section at runtime. (Target: `internal/fetchsvc/service.go`)
3. **Add regression test covering runtime skill injection**: Add or update test cases in internal/config/config_test.go or internal/harness/lint_test.go to verify that harness-declared skills are correctly parsed and injected into the agent prompt frontmatter. (Target: `internal/config/config_test.go`)
4. **Run test suite to verify the changes**: Execute the package tests to confirm that dynamic skill injection works as expected without causing regressions. (Target: `None`)

## 5. Educational Concepts
### YAML Frontmatter Injection
- **What is it:** Programmatically modifying the metadata header of a Markdown document before parsing or execution.
- **Why it matters:** Allows configuration values like active skills to be cleanly propagated into static prompt templates without rewriting prompt body text.
- **Connection to Issue:** Directly implements the solution of injecting harness-listed skill names into agent prompt frontmatter.

### Harness Configuration & Skill Activation
- **What is it:** Defining agent behavior, environment settings, and associated skills through declarative harness specifications.
- **Why it matters:** Ensures agents execute with the correct contextual constraints and style guidelines across different runs.
- **Connection to Issue:** Connects the skills declared in a harness configuration to how agents consume them at runtime.

