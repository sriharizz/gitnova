# GitNova — Supervised Fine-Tuning (QLoRA) Experiment Summary

**Experiment Name:** `gitnova-candidate-fit-qlora-v1`  
**Dataset:** 600 issues across 73 repositories in 20 programming languages.  
**Leakage-Safe Splitting:** 420 Train (49 repos) / 90 Validation (14 repos) / 90 Test (10 repos).  
**Repository-Holdout Status:** **`PASS`** (Zero repository overlap across splits).  

---

## 1. Model Comparison on Held-Out Test Set (90 Issues from 10 Unseen Repos)

| Model / Baseline | Accuracy | Macro Precision | Macro Recall | Macro F1 |
| :--- | :--- | :--- | :--- | :--- |
| **Zero-Shot Base Qwen2.5-Coder-0.5B** | 27.78% | 22.46% | 34.25% | 20.96% |
| **TF-IDF + Logistic Regression (Balanced)** | 63.33% | 61.20% | 59.80% | 60.10% |
| **GitNova Fine-Tuned QLoRA Adapter** | **82.22%** | **82.08%** | **78.52%** | **79.41%** |

---

## 2. QLoRA Per-Class Breakdown

| Class Label | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **`HIGH_FIT`** | 82.76% | 96.00% | **88.89%** | 50 |
| **`MEDIUM_FIT`** | 77.78% | 53.85% | **63.64%** | 26 |
| **`LOW_FIT`** | 85.71% | 85.71% | **85.71%** | 14 |

---

## 3. Training Configuration & Efficiency
- **Base Architecture**: `Qwen/Qwen2.5-Coder-0.5B-Instruct`
- **LoRA Parameters**: `r=16`, `alpha=32`, `dropout=0.05`, target modules: `q_proj, v_proj, k_proj, o_proj, gate_proj, up_proj, down_proj`.
- **Training Duration**: 845.54 seconds (~14.1 minutes) on 1x GPU with gradient checkpointing.
