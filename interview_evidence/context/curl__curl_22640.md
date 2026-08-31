# Issue Context Dossier: `curl/curl` #22640

**Title:** curl CPU usage waiting for input from stdin  
**Repository:** https://github.com/curl/curl  
**Language:** C  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Curl uses a small sleep or non-blocking wait of 1 millisecond in its stdin progress/readbusy callback when reading from stdin without data available, which causes unnecessary CPU utilization (around 1%) when waiting for input on Windows and other platforms.

## 2. Root Cause Analysis
> In src/config2setopts.c, CURLOPT_XFERINFOFUNCTION is registered to tool_readbusy_cb for stdin reading. Inside tool_readbusy_cb, when no new data arrives, it executes a 1-millisecond sleep/wait loop to unpause frequently, resulting in high polling frequency and continuous CPU usage.

## 3. Grounded Code Locations & Citations
- File: `src/config2setopts.c` (Lines: `806-820`) | Symbol: `config2setopts` | Role: *Registers tool_readbusy_cb as the progress callback when uploading/reading from stdin.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect tool_readbusy_cb and stdin callback registration**: Inspect symbol tool_readbusy_cb and its registration in src/config2setopts.c to understand how the 1-millisecond sleep/wait loop is currently structured when reading from stdin. (Target: `src/config2setopts.c`)
2. **Adjust polling interval or sleep duration**: Modify the delay/wait mechanism inside tool_readbusy_cb to increase the sleep or timeout duration (e.g. to a higher value like 10ms or 50ms, or use proper blocking/event-driven readiness checks) to eliminate high CPU utilization. (Target: `src/config2setopts.c`)
3. **Verify compilation and test execution**: Rebuild the curl tool and ensure that stdin reading and progress/readbusy callbacks operate correctly without breaking existing file upload or stdin streaming functionality. (Target: `src/config2setopts.c`)

## 5. Educational Concepts
### Non-Blocking I/O Polling
- **What is it:** A technique where a program repeatedly checks if data is ready rather than blocking indefinitely.
- **Why it matters:** Polling too frequently (e.g., every 1 millisecond) forces the CPU to wake up constantly, leading to noticeable CPU usage even when idle.
- **Connection to Issue:** The stdin readbusy callback polls too aggressively with a 1ms timeout, causing unnecessary CPU load while waiting for user input.

### Callback Functions in libcurl
- **What is it:** Custom user functions hooked into curl to handle events like progress updates or data transfers.
- **Why it matters:** Understanding how callbacks are invoked during transfers helps control timing and state transitions during reads and writes.
- **Connection to Issue:** tool_readbusy_cb acts as a special progress callback invoked during non-blocking stdin reads to unpause data flow.

