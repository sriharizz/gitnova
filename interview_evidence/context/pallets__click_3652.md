# Issue Context Dossier: `pallets/click` #3652

**Title:** Automatically append ellipsis (`...`) to metavars when `multiple=True` in options  
**Repository:** https://github.com/pallets/click  
**Language:** Python  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When a command-line option is configured with `multiple=True`, the auto-generated help text does not visually indicate that the option can be repeated. This issue proposes automatically appending an ellipsis (`...`) to the option's metavar (e.g., changing `--foo TEXT` to `--foo TEXT...`) to follow standard CLI conventions for repeatable options.

## 2. Root Cause Analysis
> The `Option` class in `src/click/core.py` does not override the `make_metavar` method from `Parameter`. When `Option.get_help_record` formats the option's help record, it calls `self.make_metavar(ctx=ctx)`. Because there is no option-specific implementation, it falls back to the default `Parameter.make_metavar` which does not append an ellipsis for `multiple=True`. In contrast, `Argument` overrides `make_metavar` to append `...` when `self.nargs != 1`.

## 3. Grounded Code Locations & Citations
- File: `src/click/core.py` (Lines: `2858-3660`) | Symbol: `Option` | Role: *The Option class where make_metavar should be overridden to append an ellipsis when multiple=True.* (Verified: True)
- File: `src/click/core.py` (Lines: `3411-3453`) | Symbol: `Option.get_help_record` | Role: *The method that calls self.make_metavar(ctx=ctx) to format the option's help record.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Option and Parameter classes in src/click/core.py**: Examine the `Option` class and its parent `Parameter` class in `src/click/core.py`. Note how `Parameter.make_metavar` generates the default metavar and how `Option.get_help_record` uses it. (Target: `src/click/core.py`)
2. **Override make_metavar in Option class**: Implement `make_metavar` in the `Option` class in `src/click/core.py`. It should call `super().make_metavar(ctx)` to get the base metavar, and if `self.multiple` is `True` and the metavar is not empty, append `...` to it. (Target: `src/click/core.py`)
3. **Add regression tests in tests/test_help.py**: Add a new test case in `tests/test_help.py` that defines a command with an option configured with `multiple=True`. Verify that the generated help text displays the option's metavar with `...` appended (e.g., `--foo TEXT...`). (Target: `tests/test_help.py`)
4. **Run tests and verify formatting**: Execute the test suite using pytest to ensure the new test passes and no existing help formatting tests are broken. (Target: `tests/test_help.py`)

## 5. Educational Concepts
### Metavar (Meta-variable)
- **What is it:** A placeholder string (such as TEXT, INT, or PATH) used in command-line help menus to represent the expected type or format of an option or argument value.
- **Why it matters:** Metavars guide users on what kind of input a command expects, making the command-line interface self-documenting and user-friendly.
- **Connection to Issue:** The issue requires modifying the metavar of an Option to append '...' when the option accepts multiple values, visually indicating repeatability to the user.

### Method Overriding in Class Hierarchies
- **What is it:** An object-oriented programming technique where a subclass provides a specific implementation of a method that is already defined in its superclass.
- **Why it matters:** It allows specialized behavior for subclasses (like Option or Argument) while reusing common logic from the base class (Parameter).
- **Connection to Issue:** Option needs to override make_metavar from Parameter to add custom behavior (appending '...' for multiple options) while still leveraging the base class's metavar generation logic via super().make_metavar(ctx).

