# Issue Context Dossier: `psf/requests` #7564

**Title:** raise FileNotFoundError for missing TLS material  
**Repository:** https://github.com/psf/requests  
**Language:** Python  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> The issue is about changing the existing OSError for missing TLS material to FileNotFoundError in the 'psf/requests' repository.

## 2. Root Cause Analysis
> The current implementation raises an OSError when the TLS certificate file is missing, but the developer wants to handle FileNotFoundError specifically to compare the .filename attribute.

## 3. Grounded Code Locations & Citations
- File: `src/requests/exceptions.py` (Lines: ``) | Symbol: `None` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
- Follow repository standard guidelines.

## 5. Educational Concepts
### FileNotFoundError
- **What is it:** A specific exception raised when a file is not found.
- **Why it matters:** It allows for more precise error handling and comparison of the .filename attribute.
- **Connection to Issue:** The developer wants to raise FileNotFoundError instead of OSError for missing TLS material.

### OSError
- **What is it:** A general exception raised for operating system-related errors.
- **Why it matters:** It is the current exception being raised for missing TLS material, but it is not specific enough for the developer's needs.
- **Connection to Issue:** The developer wants to replace OSError with FileNotFoundError for missing TLS material.

