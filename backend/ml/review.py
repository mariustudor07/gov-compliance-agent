"""Review the flagged labels in data/labels.csv one sentence at a time.

Run it in PyCharm (right-click -> Run 'review'). For each sentence, type:
    Enter        keep the current label
    1-9          change to that label
    6+4          main label 6, also covers 4 (saved in `also`; not used for training yet)
    s            skip (unsure) - stays flagged so you can come back to it
    b            go back one sentence
    q            save and quit (you can carry on later, it remembers where you got to)

Every answer is saved straight away. Reviewed rows get needs_review = False and human_checked = True.
"""
import csv
import re
import textwrap
from pathlib import Path

from ml.label import LABEL_GUIDE

PATH = Path(__file__).resolve().parents[2] / "data" / "labels.csv"
LABELS = list(LABEL_GUIDE)


def load():
    with PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r.setdefault("human_checked", "False")
        r.setdefault("also", "")
    return rows


def save(rows):
    with PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sentence", "label", "second_opinion", "needs_review",
                                               "human_checked", "also", "source"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = load()
    todo = [i for i, r in enumerate(rows) if r["needs_review"] == "True"]
    menu = "\n".join(f"  {n}  {label:15} {LABEL_GUIDE[label]}" for n, label in enumerate(LABELS, 1))

    pos = 0
    while pos < len(todo):
        r = rows[todo[pos]]
        print("\n" + "=" * 90)
        print(f"Sentence {pos + 1} of {len(todo)}    (from {r['source']})\n")
        print(textwrap.fill(r["sentence"], 88, initial_indent="    ", subsequent_indent="    "))
        print(f"\n  Current label:   {r['label'].upper()}" + (f"  (also: {r['also']})" if r["also"] else ""))
        print(f"  Keyword rules:   {r['second_opinion']}\n")
        print(menu)
        answer = input("\nEnter = keep, 1-9 = change, 6+4 = main + also, s = skip, b = back, q = save & quit > ")
        answer = answer.strip().lower()

        if answer == "q":
            break
        if answer == "b":
            pos = max(0, pos - 1)
            continue
        if answer == "s":
            pos += 1
            continue
        numbers = re.split(r"[\s,+]+", answer) if answer else []
        if numbers and all(n.isdigit() and 1 <= int(n) <= len(LABELS) for n in numbers):
            r["label"] = LABELS[int(numbers[0]) - 1]
            r["also"] = ";".join(LABELS[int(n) - 1] for n in numbers[1:])
        elif answer:
            print("  ?? Type Enter, a number 1-9 (or two like 6+4), s, b or q")
            continue
        r["needs_review"] = "False"
        r["human_checked"] = "True"
        save(rows)
        pos += 1

    save(rows)
    left = sum(r["needs_review"] == "True" for r in rows)
    print(f"\nSaved. {len(todo) - left} reviewed this session, {left} still to review.")


if __name__ == "__main__":
    main()
