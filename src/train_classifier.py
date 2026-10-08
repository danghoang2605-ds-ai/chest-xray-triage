"""Stage 1: ResNet normal/abnormal gate."""
import argparse
import time
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader

from src.config import load_config
from src.dataset import CXRDataset
from src.models import build_classifier, predict_probs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    cfg = load_config(p.parse_args().config)
    c = cfg["classifier"]
    torch.manual_seed(cfg["data"]["seed"])

    labels = pd.read_csv(Path(cfg["data"]["out_dir"]) / "labels.csv")
    tr, va = labels[labels.split == "train"], labels[labels.split == "val"]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    amp = device == "cuda"
    dl_tr = DataLoader(CXRDataset(tr, c["img_size"], train=True), batch_size=c["batch_size"],
                       shuffle=True, num_workers=c["num_workers"], pin_memory=amp, drop_last=True)
    dl_va = DataLoader(CXRDataset(va, c["img_size"], train=False), batch_size=c["batch_size"] * 2,
                       num_workers=c["num_workers"], pin_memory=amp)

    model = build_classifier(c["arch"]).to(device)
    # ~70% of VinDr images are "No finding": reweight positives
    pos_rate = tr["abnormal"].mean()
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(1 - pos_rate) / pos_rate], device=device))
    opt = torch.optim.AdamW(model.parameters(), lr=c["lr"], weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=c["epochs"] * len(dl_tr))
    scaler = torch.amp.GradScaler("cuda", enabled=amp)

    out = Path(c["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    best, history = -1.0, []
    for epoch in range(1, c["epochs"] + 1):
        model.train()
        t0, total = time.time(), 0.0
        for x, y in dl_tr:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast(device_type=device, enabled=amp):
                loss = crit(model(x).squeeze(1), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            total += loss.item() * len(x)

        y_va, p_va = predict_probs(model, dl_va, device)
        auc = float(roc_auc_score(y_va, p_va))
        train_loss = total / len(dl_tr.dataset)
        print(f"epoch {epoch:02d} | loss {train_loss:.4f} | val AUC {auc:.4f} | {time.time() - t0:.0f}s")
        history.append({"epoch": epoch, "train_loss": train_loss, "val_auc": auc,
                        "lr": opt.param_groups[0]["lr"]})
        pd.DataFrame(history).to_csv(out.parent / "history.csv", index=False)
        if auc > best:
            best = auc
            torch.save({"state_dict": model.state_dict(), "arch": c["arch"],
                        "img_size": c["img_size"], "val_auc": auc, "epoch": epoch}, out)
    print(f"best val AUC {best:.4f} -> {out}")


if __name__ == "__main__":
    main()
