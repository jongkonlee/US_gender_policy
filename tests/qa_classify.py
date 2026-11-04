"""Check the women's-policy rules against the compact bill copies on the qa-cache branch.

  git fetch origin qa-cache && git worktree add /tmp/qa origin/qa-cache
  python tests/qa_classify.py /tmp/qa [congress ...]
"""
import collections
import gzip
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))
import classify as C  # noqa: E402


def load(d, c):
    with gzip.open(os.path.join(d, f"bills_{c}.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            b = json.loads(line)
            b["subj"] = b.get("subj", []) + ["?"] * max(0, b.get("nsubj", 0) - len(b.get("subj", [])))
            yield b


def main():
    d = sys.argv[1]
    cs = [int(x) for x in sys.argv[2:]] or list(range(111, 120))
    random.seed(7)
    for c in cs:
        bills = list(load(d, c))
        res = [(b, C.classify_bill(b)) for b in bills]
        inc = [(b, r) for b, r in res if r.get("include")]
        cnt = collections.Counter((r["scope"], r["commem"]) for _, r in inc)
        tops = collections.Counter(r["topics"][0] for _, r in inc if r["scope"] == "core" and not r["commem"])
        print(f"== {c}: {len(bills)} bills, included {len(inc)} {dict(cnt)}")
        print("   core topics:", dict(tops.most_common()))
        weak = [(b, r) for b, r in inc if r["topics"][0] == "rights_other" and not r["commem"]]
        print(f"   rights_other (non-commem) sample of {len(weak)}:")
        for b, r in random.sample(weak, min(12, len(weak))):
            print("     ", b["id"], b["title"][:100], "|", r["basis"][:1])
        amd = []
        for b in bills:
            for num, txt in b.get("amdts", []):
                x = C.classify_text(txt, b.get("pa", ""))
                if x:
                    amd.append((b["id"], num, txt[:110], x["topics"][:2], x["dir"]))
        print(f"   amendments matched: {len(amd)}")
        for a in random.sample(amd, min(12, len(amd))):
            print("     ", a)


if __name__ == "__main__":
    main()
