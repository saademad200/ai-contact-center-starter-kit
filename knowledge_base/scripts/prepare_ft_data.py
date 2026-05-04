"""
Fine-Tuning Data Preparation Script
=====================================
Converts raw scraped text files (FAQs, T&Cs, Policies) into
OpenAI JSONL fine-tuning format locally for review before uploading to S3.

This is the LOCAL version of what the Lambda does automatically in prod.

Usage:
    python knowledge_base/scripts/prepare_ft_data.py
"""

import json
import re
from pathlib import Path

RAW_DIR = Path("knowledge_base/docs/faqs")
OUTPUT_DIR = Path("knowledge_base/docs/finetuning")
OUTPUT_FILE = OUTPUT_DIR / "training.jsonl"

SYSTEM_PROMPT = (
    "You are Alfalah GPT, a helpful and professional customer support AI "
    "for Alfalah Investments. You assist customers with questions about "
    "mutual funds, investment accounts, policies, and Shariah-compliant investing. "
    "Be concise, accurate, and always add the disclaimer "
    "'Past performance is not indicative of future results.' when discussing fund returns."
)


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"Page \d+ of \d+", "", text, flags=re.IGNORECASE)
    return text.strip()


def split_into_qa_pairs(text: str) -> list[dict]:
    """
    Heuristic: splits text at Q:/A: patterns or numbered questions.
    Falls back to paragraph-level chunks if no Q&A pattern found.
    """
    pairs = []

    # Try to match "Q: ... A: ..." or "Question: ... Answer: ..." patterns
    qa_pattern = re.compile(
        r"(?:Q[:\.]?\s*|Question[:\s]+)(.*?)\n+(?:A[:\.]?\s*|Answer[:\s]+)(.*?)(?=\n+Q[:\.]?\s*|\n+Question[:\s]+|$)",
        re.DOTALL | re.IGNORECASE,
    )
    matches = qa_pattern.findall(text)

    if matches:
        for question, answer in matches:
            q = question.strip()
            a = answer.strip()
            if q and a and len(a) > 20:
                pairs.append({"user": q, "assistant": a})
        return pairs

    # Fallback: split by double newlines — treat every 2 paragraphs as a Q/A
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
    for i in range(0, len(paragraphs) - 1, 2):
        pairs.append({"user": paragraphs[i], "assistant": paragraphs[i + 1]})

    return pairs


def to_jsonl_entry(user: str, assistant: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    txt_files = list(RAW_DIR.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {RAW_DIR}. Run seed.py first.")
        return

    all_entries = []
    for txt_file in txt_files:
        print(f"Processing {txt_file.name} ...")
        raw = txt_file.read_text(encoding="utf-8")
        text = clean_text(raw)
        pairs = split_into_qa_pairs(text)
        print(f"  → {len(pairs)} Q/A pairs extracted")
        for pair in pairs:
            all_entries.append(to_jsonl_entry(pair["user"], pair["assistant"]))

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\nDone! {len(all_entries)} fine-tuning examples written to {OUTPUT_FILE}")
    print("Next: upload this file via the Admin Panel → S3 raw/ → Lambda processes it")
    print("  OR: run `make finetune` to trigger directly via OpenAI API")


if __name__ == "__main__":
    main()
