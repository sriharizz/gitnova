# Issue Context Dossier: `fullsend-ai/fullsend` #6533

**Title:** Add `providers.allow` config for per-repo provider allowlisting  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Design and track a new `providers.allow` configuration option in `.fullsend/config.yaml` to support per-repo provider allowlists once multi-provider support lands.

## 2. Root Cause Analysis
> This is a feature-tracking and design task stemming from the runtime parity backlog (#6527), intended to prepare the configuration surface before multi-provider support (GPT / Azure OpenAI / Bedrock) is added.

## 3. Grounded Code Locations & Citations
- File: `internal/config/config.go` (Lines: `176-215`) | Symbol: `ValidProviders` | Role: *Defines recognized inference providers in config* (Verified: True)
- File: `internal/config/config.go` (Lines: `106-145`) | Symbol: `PerRepoInferenceConfig` | Role: *Defines inference backend settings for per-repo configs* (Verified: True)
- File: `internal/config/interfaces.go` (Lines: `491-530`) | Symbol: `SetInferenceProvider` | Role: *Provides interface setters for inference configuration* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect configuration structs in internal/config/config.go**: Inspect the PerRepoInferenceConfig struct and ValidProviders slice in internal/config/config.go to understand where to add the new allowlist configuration property. (Target: `internal/config/config.go`)
2. **Add providers.allow property to configuration structures**: Define the allowlist field within PerRepoInferenceConfig in internal/config/config.go to support per-repo provider allowlisting. (Target: `internal/config/config.go`)
3. **Update interface setters in internal/config/interfaces.go**: Update SetInferenceProvider and related configuration interface definitions in internal/config/interfaces.go to accommodate the new allow configuration option. (Target: `internal/config/interfaces.go`)
4. **Implement unit tests in internal/config/config_test.go**: Add unit tests in internal/config/config_test.go and internal/config/defaults_test.go validating that the new providers.allow configuration option parses and defaults correctly. (Target: `internal/config/config_test.go`)

## 5. Educational Concepts
### Configuration Schema Design
- **What is it:** The process of defining structures, fields, and validation rules in configuration files like YAML.
- **Why it matters:** Proper schema design ensures that user configurations are correctly parsed, validated, and mapped into application data structures without runtime errors.
- **Connection to Issue:** This issue requires designing the new `providers.allow` configuration field within `.fullsend/config.yaml` and defining its validation rules.

### Allowlist Security Controls
- **What is it:** A security mechanism that explicitly permits approved entities while denying all others by default.
- **Why it matters:** Allowlists prevent unauthorized access or resource usage by restricting execution or communication to known safe endpoints and providers.
- **Connection to Issue:** The `providers.allow` setting acts as an explicit allowlist for inference providers per repository, succeeding the sandbox egress profile.

