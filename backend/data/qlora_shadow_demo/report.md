# GitNova — QLoRA Model READ-ONLY Shadow Evaluation Report

**Evaluation Mode:** READ-ONLY Shadow Integration (Zero Production Impact)  
**Base Model:** `Qwen/Qwen2.5-Coder-0.5B-Instruct`  
**Adapter:** [`backend/data/dataset_collection/final_v1/models/gitnova-qwen-qlora-v1`](file:///c:/gitNova/backend/data/dataset_collection/final_v1/models/gitnova-qwen-qlora-v1)  
**Execution Timestamp:** 2026-08-31T15:24:31.015542+00:00  

---

## 1. Executive Summary

- **Total Issues Evaluated:** **16**
- **Overall Agreement Rate with Production Decision:** **12.5%** (2 / 16)
- **QLoRA Predictions by Class:**
  - **`HIGH_FIT`**: **1** (6.2%)
  - **`MEDIUM_FIT`**: **14** (87.5%)
  - **`LOW_FIT`**: **1** (6.2%)
- **Average Inference Latency:** **839.01 ms**

---

## 2. 5 Representative Shadow Evaluation Examples

### Example 1: `pallets/click #2645`
- **Title:** tests: add test coverage for float and int param type coercion error messages
- **Existing Production Decision:** `HIGH_FIT` (Published: `True`)
- **QLoRA Shadow Prediction:** `MEDIUM_FIT` (2177.89ms)
- **Status:** `DISAGREE`
- **Analysis:** QLoRA predicted a more conservative fit tier than the production heuristic.

### Example 2: `pallets/click #2853`
- **Title:** The call stack is displayed when an exception is returned when an invalid parameter is displayed during command line association.
- **Existing Production Decision:** `HIGH_FIT` (Published: `True`)
- **QLoRA Shadow Prediction:** `HIGH_FIT` (629.03ms)
- **Status:** `AGREE`
- **Analysis:** Both production heuristic gates and QLoRA classified this as a high-confidence candidate.

### Example 3: `nexu-io/open-design #7608`
- **Title:** pi-ai 0.84.3: provider catalog data shipped as JavaScript inside .json files breaks CJS consumers
- **Existing Production Decision:** `HIGH_FIT` (Published: `True`)
- **QLoRA Shadow Prediction:** `MEDIUM_FIT` (843.2ms)
- **Status:** `DISAGREE`
- **Analysis:** QLoRA predicted a more conservative fit tier than the production heuristic.

### Example 4: `paradedb/paradedb #6104`
- **Title:** Range-partitioned JoinScan converts sampled NUMERIC partition bounds twice
- **Existing Production Decision:** `HIGH_FIT` (Published: `True`)
- **QLoRA Shadow Prediction:** `MEDIUM_FIT` (751.83ms)
- **Status:** `DISAGREE`
- **Analysis:** QLoRA predicted a more conservative fit tier than the production heuristic.

### Example 5: `clap-rs/clap #6471`
- **Title:** Error::render() doc example teaches a color-stripping path — println!("{err}") is always plain
- **Existing Production Decision:** `HIGH_FIT` (Published: `True`)
- **QLoRA Shadow Prediction:** `MEDIUM_FIT` (795.54ms)
- **Status:** `DISAGREE`
- **Analysis:** QLoRA predicted a more conservative fit tier than the production heuristic.


---

## 3. Disagreement Case Analysis (14 Cases)

| Repository | Issue # | Existing Prod Decision | QLoRA Prediction | Title | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pallets/click` | `#2645` | `HIGH_FIT` | **`MEDIUM_FIT`** | tests: add test coverage for float and int pa... | 2177.89ms |
| `nexu-io/open-design` | `#7608` | `HIGH_FIT` | **`MEDIUM_FIT`** | pi-ai 0.84.3: provider catalog data shipped a... | 843.2ms |
| `paradedb/paradedb` | `#6104` | `HIGH_FIT` | **`MEDIUM_FIT`** | Range-partitioned JoinScan converts sampled N... | 751.83ms |
| `clap-rs/clap` | `#6471` | `HIGH_FIT` | **`MEDIUM_FIT`** | Error::render() doc example teaches a color-s... | 795.54ms |
| `expressjs/express` | `#7362` | `HIGH_FIT` | **`MEDIUM_FIT`** | res.send(ArrayBuffer) silently sends {} as JS... | 735.94ms |
| `scikit-learn/scikit-learn` | `#34668` | `HIGH_FIT` | **`MEDIUM_FIT`** | RandomForest errors out with infinite values ... | 777.71ms |
| `expressjs/express` | `#7350` | `HIGH_FIT` | **`MEDIUM_FIT`** | res.render()/app.render() throws opaque TypeE... | 752.35ms |
| `alibaba/zvec` | `#609` | `LOW_FIT` | **`MEDIUM_FIT`** | [Feature]: java是真的不行了吗？为什么没有java的SDK。... | 779.13ms |
| `eclipse-apoapsis/ort-server` | `#5729` | `LOW_FIT` | **`MEDIUM_FIT`** | Fix UI formatting glitches in the runs table... | 741.7ms |
| `yschimke/compose-ai-tools` | `#4220` | `LOW_FIT` | **`MEDIUM_FIT`** | preview server: m3-catalog's live render lane... | 777.34ms |
| `alibaba/nacos` | `#2272` | `LOW_FIT` | **`MEDIUM_FIT`** | Batch offline service based on IP address... | 745.82ms |
| `unslothai/unsloth` | `#9697` | `LOW_FIT` | **`MEDIUM_FIT`** | [Bug] KV cache quantization is not reflected ... | 769.2ms |
| `yschimke/compose-ai-tools` | `#4097` | `LOW_FIT` | **`MEDIUM_FIT`** | `SharedElementFilmstripPreview` is not determ... | 798.75ms |
| `tsouza/cerberus` | `#2355` | `LOW_FIT` | **`MEDIUM_FIT`** | compatibility/prometheus-floor: thin timing m... | 710.33ms |

---

## 4. How to Reproduce this Shadow Demo Live

You can re-run this shadow evaluation anytime using this single command:
```bash
python backend/scripts/evaluation/run_qlora_shadow_eval.py
```

---

## 5. Verification Checklist
- [x] Production publication decisions strictly unchanged.
- [x] Existing frontend behavior strictly unchanged.
- [x] RAG retrieval strictly unchanged.
- [x] Gemini prompts strictly unchanged.
- [x] QLoRA adapter loaded and evaluated on real candidate issues.
