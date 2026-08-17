import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

try:
    from backend.scripts.run_gitnova_qlora_experiment import evaluate_base_llm, CLASSES
except ImportError:
    from scripts.run_gitnova_qlora_experiment import evaluate_base_llm, CLASSES


def main():
    parser = argparse.ArgumentParser(description="Evaluate GitNova QLoRA / Base Model on candidate issues")
    parser.add_argument("--model-path", type=str, required=True, help="Base model ID or path to adapter")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-Coder-0.5B-Instruct", help="Base model ID")
    parser.add_argument("--test-file", type=str, default="backend/data/dataset_collection/final_v1/test.jsonl")
    parser.add_argument("--is-adapter", action="store_true", help="Flag if model-path is a LoRA adapter")
    parser.add_argument("--output-json", type=str, default="backend/data/dataset_collection/final_v1/eval_metrics.json")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading test records from {args.test_file}...")
    records = []
    with open(args.test_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if args.is_adapter:
        print(f"Loading base model {args.base_model} and adapter {args.model_path}...")
        base = AutoModelForCausalLM.from_pretrained(args.base_model, torch_dtype=torch.float32, trust_remote_code=True).to(device)
        model = PeftModel.from_pretrained(base, args.model_path).to(device)
    else:
        print(f"Loading base model {args.model_path}...")
        model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.float32, trust_remote_code=True).to(device)

    metrics, preds = evaluate_base_llm(model, tokenizer, records, device)
    print("\n================ EVALUATION METRICS ================")
    print(f"Accuracy:        {metrics['accuracy']:.4f}")
    print(f"Macro Precision: {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:    {metrics['macro_recall']:.4f}")
    print(f"Macro F1:        {metrics['macro_f1']:.4f}")
    print("Per Class:")
    for cls, val in metrics["per_class"].items():
        print(f"  {cls:<12} Precision: {val['precision']:.4f} | Recall: {val['recall']:.4f} | F1: {val['f1']:.4f} (Support: {val['support']})")

    out_p = Path(args.output_json)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved evaluation metrics to {out_p}")


if __name__ == "__main__":
    main()
