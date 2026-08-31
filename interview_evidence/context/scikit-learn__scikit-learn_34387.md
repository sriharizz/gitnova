# Issue Context Dossier: `scikit-learn/scikit-learn` #34387

**Title:** `OrdinalEncoder` surprising behavior: missing values are treated as unknown categories first  
**Repository:** https://github.com/scikit-learn/scikit-learn  
**Language:** Python  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> In `OrdinalEncoder`, when transforming data containing missing values (like `np.nan`), the encoder can incorrectly treat these missing values as 'unknown categories' instead of 'missing values'. This happens if the missing value was not present during the `fit` phase, or if the input has an `object` data type. As a result, instead of mapping the missing value to the configured `encoded_missing_value` (e.g., `np.nan`), the encoder either raises an error or maps it to the `unknown_value` (e.g., `-1`).

## 2. Root Cause Analysis
> The root cause is that `OrdinalEncoder` (and its parent/helper classes in `sklearn/preprocessing/_encoders.py`) performs unknown category detection before or in a way that interferes with missing value handling. Specifically, during `transform`, the encoder checks if the input values are present in the fitted `categories_`. Since `np.nan` is not in `categories_` (if it wasn't in the training data), it is flagged as an unknown category. The code then applies the `handle_unknown` strategy (either raising an error or mapping to `unknown_value`), completely bypassing the missing value mapping. Furthermore, for `object` dtype arrays, `np.nan` comparison (`np.nan == np.nan` is `False`) causes standard equality checks and search operations to fail or behave inconsistently, leading to unexpected `ValueError` exceptions even when `np.nan` was present during `fit`.

## 3. Grounded Code Locations & Citations
- File: `sklearn/impute/_base.py` (Lines: `95-168`) | Symbol: `_get_mask` | Role: *Provides reference implementation for missing value masking and handling in scikit-learn.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect transform control flow in _encoders.py**: Inspect the `_transform` method of `_BaseEncoder` and `OrdinalEncoder` in `sklearn/preprocessing/_encoders.py` to understand how missing values and unknown categories are currently identified and processed during transformation. (Target: `sklearn/preprocessing/_encoders.py`)
2. **Mask missing values before unknown category check**: Modify the transformation logic in `sklearn/preprocessing/_encoders.py` to compute a missing value mask for the input data using `_get_mask` or equivalent. Ensure that any elements identified as missing values are excluded from the unknown category detection checks. (Target: `sklearn/preprocessing/_encoders.py`)
3. **Map missing values to encoded_missing_value**: Ensure that the masked missing values are directly mapped to the configured `encoded_missing_value` (e.g., `np.nan`) in the output array, bypassing any `handle_unknown` logic, even if the missing value was not seen during the `fit` phase or if the input array has an `object` dtype. (Target: `sklearn/preprocessing/_encoders.py`)
4. **Add regression tests for OrdinalEncoder missing values**: Add a new test case in `sklearn/preprocessing/tests/test_encoders.py` that instantiates `OrdinalEncoder` with various configurations of `handle_unknown` and `unknown_value`, fits it on data without missing values, and transforms data containing missing values (including `object` dtype arrays with `np.nan`), asserting that they are correctly mapped to `encoded_missing_value` without raising errors. (Target: `sklearn/preprocessing/tests/test_encoders.py`)
5. **Run the encoder test suite**: Execute the test suite for encoders to verify that the new tests pass and no regressions are introduced in existing encoder functionality. (Target: `sklearn/preprocessing/tests/test_encoders.py`)

## 5. Educational Concepts
### Decoupling Missing Values from Unknown Categories
- **What is it:** Ensuring that missing values (like `NaN` or `None`) are detected and handled separately from actual unseen/unknown categories during data transformation.
- **Why it matters:** If missing values are treated as unknown categories, they will be incorrectly mapped to the unknown value placeholder (e.g., `-1`) or raise validation errors, which breaks pipelines that expect missing values to be preserved or imputed later.
- **Connection to Issue:** In `OrdinalEncoder`, missing values should be masked and mapped to `encoded_missing_value` first, before any unknown category checks are performed, preventing them from being treated as unknown categories.

### NaN Handling in Object Arrays
- **What is it:** Managing floating-point `NaN` values within NumPy arrays of `object` dtype, where standard equality checks (`val == nan`) fail because `NaN` is not equal to itself.
- **Why it matters:** In Python/NumPy, `np.nan != np.nan`. When arrays have `object` dtype, element-wise comparisons or membership checks (like `in` or `np.unique`) can fail to identify `NaN` correctly unless specialized functions like `is_scalar_nan` or `_get_mask` are used.
- **Connection to Issue:** The bug where `OrdinalEncoder` raises an error on `object` dtype arrays containing `np.nan` is caused by incorrect comparison/identification of `NaN` values in object arrays during category validation.

