# Issue Context Dossier: `clap-rs/clap` #6471

**Title:** Error::render() doc example teaches a color-stripping path — println!("{err}") is always plain  
**Repository:** https://github.com/clap-rs/clap  
**Language:** Unknown  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The documentation example for `Error::render()` incorrectly teaches developers to print the returned `StyledStr` directly using `println!("{}", err.render())`. Because `StyledStr`'s `Display` implementation is color-unaware and strips ANSI escape codes, this path always outputs plain text, even on terminals that support color.

## 2. Root Cause Analysis
> The root cause is that `StyledStr` implements `std::fmt::Display` by stripping ANSI escape codes (using `anstream::adapter::strip_str` or similar under the hood) to ensure safe, plain-text fallback printing. In contrast, `Error::print()` uses a TTY-aware `Colorizer` and `anstream::AutoStream` to preserve colors when appropriate. The documentation example for `Error::render()` incorrectly teaches users to print the `StyledStr` directly via `Display`, which bypasses the color-preserving path and always strips colors.

## 3. Grounded Code Locations & Citations
- *General repository target scope*

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Error::render documentation**: Locate the `Error::render` method in `clap_builder/src/error/mod.rs` and inspect its doc comments and code examples. (Target: `clap_builder/src/error/mod.rs`)
2. **Update the documentation example**: Modify the code example in the doc comment of `Error::render` to show how to print the rendered error with colors preserved (e.g., using `err.render().ansi()` or recommending `err.print()`), and add a note explaining that the default `Display` implementation of `StyledStr` strips ANSI escape codes. (Target: `clap_builder/src/error/mod.rs`)
3. **Verify StyledStr methods**: Check `clap_builder/src/builder/styled_str.rs` to ensure that `.ansi()` or the recommended method is indeed available on `StyledStr` and behaves as documented. (Target: `clap_builder/src/builder/styled_str.rs`)
4. **Run tests and lints**: Run `cargo test` and `cargo clippy` to ensure that the documentation code examples compile successfully and no lints are violated. (Target: `None`)

## 5. Educational Concepts
### StyledStr and Color-Unaware Display
- **What is it:** In clap, `StyledStr` represents a string that can contain styling/color information. However, its `Display` implementation is designed to be color-unaware and strips ANSI escape codes to provide a safe plain-text fallback.
- **Why it matters:** Developers need to know when formatting a styled string will strip colors so they don't accidentally lose terminal styling in their application outputs.
- **Connection to Issue:** The documentation example for `Error::render()` incorrectly suggests printing the `StyledStr` directly, which triggers this color-stripping behavior.

### TTY-Aware vs. Explicit ANSI Rendering
- **What is it:** TTY-aware printing automatically detects if the output destination supports color, whereas explicit ANSI rendering (like `.ansi()`) forces the inclusion of ANSI escape codes regardless of the destination.
- **Why it matters:** Understanding the difference helps developers choose the right method for printing errors depending on whether they want automatic detection or forced styling.
- **Connection to Issue:** Updating the doc example to use `.ansi()` or explaining the difference ensures developers use the correct API for their specific use case.

