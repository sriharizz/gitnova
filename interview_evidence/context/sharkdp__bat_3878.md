# Issue Context Dossier: `sharkdp/bat` #3878

**Title:** Recursive custom syntax definition can crash MacOS due to OOM  
**Repository:** https://github.com/sharkdp/bat  
**Language:** Rust  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> A recursive custom syntax definition can cause unbounded memory allocation, leading to a kernel panic on MacOS.

## 2. Root Cause Analysis
> The issue occurs when a custom syntax definition includes a scope that collides with the scope it is trying to include, causing an infinite loop of memory allocation.

## 3. Grounded Code Locations & Citations
- File: `src/assets.rs` (Lines: ``) | Symbol: `None` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
- Follow repository standard guidelines.

## 5. Educational Concepts
### Custom Syntax Definitions
- **What is it:** Custom syntax definitions are used to define the syntax of a programming language.
- **Why it matters:** Custom syntax definitions are important for highlighting and formatting code.
- **Connection to Issue:** The issue occurs due to a recursive custom syntax definition.

### Scope Collisions
- **What is it:** Scope collisions occur when two or more scopes have the same name.
- **Why it matters:** Scope collisions can cause issues with code highlighting and formatting.
- **Connection to Issue:** The issue occurs due to a scope collision in the custom syntax definition.

