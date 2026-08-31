# Issue Context Dossier: `openai/codex` #39647

**Title:** Gmail connector stamps outgoing Date header with -0700 instead of user timezone  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When the Gmail connector sends mail via Codex Desktop, the RFC 5322 Date header uses a hardcoded or default Pacific-time timezone offset (-0700) instead of the user's actual configured account or local timezone.

## 2. Root Cause Analysis
> The message generation code or email client connector defaults to a hardcoded timezone offset (-0700) rather than querying or utilizing the user's dynamic timezone or timestamp provider (such as AppServerTimeProvider) when constructing the RFC 5322 Date header.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/app-server/src/current_time.rs` (Lines: `36-75`) | Symbol: `AppServerTimeProvider` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect AppServerTimeProvider**: Inspect AppServerTimeProvider in codex-rs/app-server/src/current_time.rs to understand how time and timezone information are currently provided to backend services. (Target: `codex-rs/app-server/src/current_time.rs`)
2. **Locate Gmail Connector Date Header Serialization**: Locate where the Gmail connector constructs the RFC 5322 Date header and replace the hardcoded -0700 timezone offset with the dynamic local or account timezone derived from AppServerTimeProvider or standard chrono local time. (Target: `codex-rs/app-server/src/current_time.rs`)
3. **Implement Dynamic Timezone Offset**: Update the email formatting logic to use chrono::Local or the time provider's offset instead of the fixed literal string '-0700', ensuring proper RFC 5322 compliance. (Target: `codex-rs/app-server/src/current_time.rs`)
4. **Add Regression Test**: Add a unit test in codex-rs/app-server/src/attestation.rs or a new test case verifying that the generated Date header reflects the correct local or expected non-hardcoded timezone offset. (Target: `codex-rs/app-server/src/attestation.rs`)
5. **Run Test Suite**: Execute cargo test to verify that all app-server and analytics tests pass successfully with the updated timezone handling. (Target: `None`)

## 5. Educational Concepts
### RFC 5322 Date Header Formatting
- **What is it:** The standard format for timestamps in internet email messages, requiring a specific date, time, and timezone offset.
- **Why it matters:** Incorrect timezone offsets in email headers lead to confusion in conversation histories, incorrect audit timelines, and mismatched sent times across mail clients.
- **Connection to Issue:** The Gmail connector hardcodes a Pacific time offset (-0700) when building the RFC 5322 Date header instead of using the user's correct local timezone offset.

### Timezone-Aware Date Serialization
- **What is it:** Handling dates and times in software while correctly preserving and converting local timezone offsets rather than defaulting to system or server zones.
- **Why it matters:** Ensures that user-facing timestamps accurately reflect the user's actual physical or account timezone across different geographical regions.
- **Connection to Issue:** Fixing the bug requires updating the timestamp serialization logic in the connector to respect the user's configured timezone or fall back to UTC.

