# Issue Context Dossier: `sharkdp/bat` #3425

**Title:** FR: use different style when showing multiple files, one file, (maybe) piped input  
**Repository:** https://github.com/sharkdp/bat  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The user wants to dynamically customize the output style of 'bat' based on the context of the inputs: specifically, using a simpler style (like plain) for a single file or stdin, and a richer style (like grid/header) when displaying multiple files. Currently, 'bat' only supports a single global style configuration.

## 2. Root Cause Analysis
> The command-line interface defined in 'src/bin/bat/clap_app.rs' only defines the '--style' option. In 'src/bin/bat/app.rs', the 'style_components' method resolves the active style components solely based on the '--style' argument, '--decorations', or '--plain' flags, without any knowledge of or reference to the number of files or input types (stdin vs. regular files) being processed.

## 3. Grounded Code Locations & Citations
- File: `src/bin/bat/clap_app.rs` (Lines: `526-565`) | Symbol: `block_526` | Role: *Defines the command-line arguments including the '--style' option.* (Verified: True)
- File: `src/bin/bat/app.rs` (Lines: `666-705`) | Symbol: `style_components` | Role: *Resolves the active style components from the parsed command-line arguments.* (Verified: True)
- File: `src/bin/bat/app.rs` (Lines: `596-635`) | Symbol: `block_596` | Role: *Parses the input files and stdin arguments into a vector of inputs.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Control Flow and Style Resolution**: Inspect `src/bin/bat/clap_app.rs` to see how `--style` is defined, and inspect `src/bin/bat/app.rs` (specifically the `style_components` method) to understand how style components are currently resolved from the parsed arguments. (Target: `src/bin/bat/app.rs`)
2. **Define New Command-Line Options**: Add `--style-single-file`, `--style-multiple-files`, and `--style-stdin` options to the clap application definition in `src/bin/bat/clap_app.rs` under the style-related arguments section. (Target: `src/bin/bat/clap_app.rs`)
3. **Update Style Resolution Logic**: Modify the `style_components` method in `src/bin/bat/app.rs` to accept the list of inputs or their count/type. Implement logic to check if `--style-single-file`, `--style-multiple-files`, or `--style-stdin` are provided, and override the default style based on whether there is a single file, multiple files, or stdin being processed. (Target: `src/bin/bat/app.rs`)
4. **Add Integration Tests and Verify**: Create integration tests in the existing test suite that execute `bat` with different combinations of inputs (single file, multiple files, stdin) and the new style override flags, asserting that the correct output decorations are rendered. Run `cargo test` to verify. (Target: `tests/integration_tests.rs`)

## 5. Educational Concepts
### Cascading Configuration Overrides
- **What is it:** A design pattern where more specific configuration options override more general ones based on runtime context.
- **Why it matters:** It allows command-line tools to have sensible, broad defaults while giving advanced users fine-grained control over specific scenarios without needing wrapper scripts.
- **Connection to Issue:** Implementing '--style-single-file' and '--style-multiple-files' requires cascading these specific style overrides over the base '--style' configuration depending on the runtime input count.

### Input Stream Context Awareness
- **What is it:** The ability of a CLI application to inspect its input sources (such as files vs. standard input) and count them before rendering output.
- **Why it matters:** It enables tools to adapt their user interface dynamically, such as hiding headers when there is only one stream to display.
- **Connection to Issue:** The application needs to count the parsed inputs and check if any are stdin to decide which style override to apply.

