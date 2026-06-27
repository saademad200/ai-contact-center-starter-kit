"""
S3 Text Processor — AWS Lambda
================================
Trigger: S3 ObjectCreated on raw/ prefix
Output:  cleaned/{filename}.jsonl in the same bucket

Flow:
  1. Download .txt file from S3 raw/ prefix.
  2. Clean text (strip page numbers, normalize whitespace).
  3. Extract Q/A pairs (regex Q:/A: match, paragraph fallback).
  4. Format each pair as an OpenAI fine-tuning JSONL entry.
  5. Upload result to S3 cleaned/{name}.jsonl.

This is the automated cloud version of:
  knowledge_base/scripts/prepare_ft_data.py
"""

import json
import os
import re
import urllib.parse

import boto3

s3 = boto3.client("s3")

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


def split_into_qa_pairs(text: str) -> list:
    """
    Extracts Q/A pairs from cleaned text.
    Primary:  regex match on Q:/A: or Question:/Answer: patterns.
    Fallback: treat every consecutive pair of paragraphs as user/assistant.
    """
    pairs = []

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

    # Fallback: every 2 paragraphs → one Q/A pair
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
    for i in range(0, len(paragraphs) - 1, 2):
        pairs.append({"user": paragraphs[i], "assistant": paragraphs[i + 1]})

    return pairs


def to_jsonl_entry(user: str, assistant: str) -> str:
    entry = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }
    return json.dumps(entry, ensure_ascii=False)


def lambda_handler(event: dict, context: object) -> dict:
    print("Received event: " + json.dumps(event, indent=2))

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    print(f"Processing: s3://{bucket}/{key}")

    try:
        # 1. Download raw .txt file
        response = s3.get_object(Bucket=bucket, Key=key)
        raw_text = response["Body"].read().decode("utf-8")
        print(f"Downloaded {len(raw_text):,} chars from {key}")

        # 2. Clean
        cleaned_text = clean_text(raw_text)

        # 3. Extract Q/A pairs
        pairs = split_into_qa_pairs(cleaned_text)
        print(f"Extracted {len(pairs)} Q/A pairs")

        if not pairs:
            print("No Q/A pairs extracted — skipping upload.")
            return {
                "statusCode": 200,
                "body": json.dumps(f"No pairs extracted from {key}"),
            }

        # 4. Format to JSONL
        jsonl_lines = [to_jsonl_entry(p["user"], p["assistant"]) for p in pairs]
        jsonl_data = "\n".join(jsonl_lines)

        # 5. Upload to cleaned/ prefix: raw/filename.txt → cleaned/filename.jsonl
        filename = os.path.basename(key)
        name, _ = os.path.splitext(filename)
        cleaned_key = f"cleaned/{name}.jsonl"

        s3.put_object(
            Bucket=bucket,
            Key=cleaned_key,
            Body=jsonl_data.encode("utf-8"),
            ContentType="application/jsonlines",
        )
        print(f"Uploaded {len(jsonl_lines)} entries to s3://{bucket}/{cleaned_key}")

        return {
            "statusCode": 200,
            "body": json.dumps(f"Processed {key} → {cleaned_key}"),
        }

    except Exception as e:
        print(f"Error processing s3://{bucket}/{key}: {e}")
        raise e
