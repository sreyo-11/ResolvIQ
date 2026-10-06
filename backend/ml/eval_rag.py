"""Usage (from backend/):  python -m ml.eval_rag"""
import json
from pathlib import Path

from app.core.config import settings
from app.repositories import kb_repo
from app.services.embeddings import get_embedder
from ml.data import connect

DATA = json.loads((Path(__file__).parent / "rag_eval_set.json").read_text(encoding="utf-8"))


def titles_and_sims(conn, emb, k=5):
    hits = kb_repo.search(conn, emb, k, 0.0)
    return [h["article_title"] for h in hits], [float(h["similarity"]) for h in hits]


def main() -> None:
    emb = get_embedder()
    hit1 = hit3 = 0
    pos_top, neg_top = [], []
    with connect() as conn:
        for item in DATA["answerable"]:
            titles, sims = titles_and_sims(conn, emb.embed_text(item["q"]))
            hit1 += titles[0] == item["title"]
            hit3 += item["title"] in titles[:3]
            pos_top.append(sims[0])
            if titles[0] != item["title"]:
                print(f"  MISS: '{item['q'][:55]}...' -> got '{titles[0]}'")
        for q in DATA["unanswerable"]:
            neg_top.append(titles_and_sims(conn, emb.embed_text(q))[1][0])

    n = len(DATA["answerable"])
    print(f"\nhit@1 = {hit1 / n:.0%}   hit@3 = {hit3 / n:.0%}  (n={n})")
    print(f"top similarity on answerable:   min={min(pos_top):.2f}  median={sorted(pos_top)[n // 2]:.2f}")
    print(f"top similarity on unanswerable: max={max(neg_top):.2f}")
    thr = settings.kb_min_similarity
    refused = sum(s < thr for s in neg_top)
    answered = sum(s >= thr for s in pos_top)
    print(f"at KB_MIN_SIMILARITY={thr}: answers {answered}/{n} answerable, refuses {refused}/{len(neg_top)} off-topic")
    print("Tip: set the threshold between the unanswerable max and the answerable min.")


if __name__ == "__main__":
    main()