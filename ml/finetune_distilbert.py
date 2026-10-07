"""Usage (inside ml/.venv-gpu):  python finetune_distilbert.py
Same hash split as backend/ml/data.py, so results are comparable with the LR models."""
import csv
import hashlib
import json
import time
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import DataLoader, TensorDataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ["billing", "account", "technical", "shipping", "integrations", "general"]
MODEL, EPOCHS, BATCH, LR, MAX_LEN = "distilbert-base-uncased", 3, 16, 5e-5, 128


def is_test(subject: str, body: str) -> bool:  # must match backend/ml/data.py
    return int(hashlib.md5(f"{subject}\n{body}".encode()).hexdigest(), 16) % 5 == 0


def encode(tok, rows):
    enc = tok([f"{r['subject']}\n{r['body']}" for r in rows], truncation=True,
              max_length=MAX_LEN, padding=True, return_tensors="pt")
    y = torch.tensor([CATEGORIES.index(r["category"]) for r in rows])
    return TensorDataset(enc["input_ids"], enc["attention_mask"], y)


def main() -> None:
    rows = list(csv.DictReader((ROOT / "data" / "tickets_synthetic.csv").open(encoding="utf-8")))
    train = [r for r in rows if not is_test(r["subject"], r["body"])]
    test = [r for r in rows if is_test(r["subject"], r["body"])]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    use_amp = dev == "cuda"  # if you see NaN loss on the 1650, set this to False (fits in fp32 too)

    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=len(CATEGORIES)).to(dev)
    tr_dl = DataLoader(encode(tok, train), batch_size=BATCH, shuffle=True)
    te_dl = DataLoader(encode(tok, test), batch_size=64)

    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    steps = EPOCHS * len(tr_dl)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    t0 = time.time()
    for epoch in range(EPOCHS):
        model.train()
        for ids, mask, y in tr_dl:
            ids, mask, y = ids.to(dev), mask.to(dev), y.to(dev)
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=use_amp):
                loss = model(input_ids=ids, attention_mask=mask, labels=y).loss
            opt.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
        print(f"epoch {epoch + 1}/{EPOCHS} last_loss={loss.item():.4f}")
    train_s = time.time() - t0

    model.eval()
    preds, gold = [], []
    with torch.no_grad():
        for ids, mask, y in te_dl:
            logits = model(input_ids=ids.to(dev), attention_mask=mask.to(dev)).logits
            preds += logits.argmax(-1).cpu().tolist()
            gold += y.tolist()
    result = {
        "model": MODEL, "test_acc": accuracy_score(gold, preds),
        "test_macro_f1": f1_score(gold, preds, average="macro"),
        "train_seconds": round(train_s, 1),
        "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2) if use_amp else None,
    }
    print(result)
    out = ROOT / "ml" / "artifacts" / "distilbert_category"
    model.save_pretrained(out)
    tok.save_pretrained(out)
    (ROOT / "docs" / "metrics").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "metrics" / "distilbert.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()