import os
import json
import urllib.parse
import boto3

s3 = boto3.client("s3")


def process_text(text: str) -> str:
    """
    Cleans the raw text by removing boilerplate T&Cs and standardizing format.
    """
    # Simple cleaning for Alfalah boilerplate (stubbed)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "Terms and Conditions" in line or "Disclaimer" in line:
            continue  # Basic skip rule
        cleaned_lines.append(line)
    return " ".join(cleaned_lines)


def convert_to_jsonl(text: str) -> str:
    """
    Converts cleaned text into OpenAI Fine-Tuning JSONL format.
    Assumes each paragraph or block could be a system/user/assistant interaction.
    For this stub, we create a generic system prompt for Alfalah and put the text as the assistant response.
    """
    system_message = {
        "role": "system",
        "content": "You are a helpful and professional customer support AI for Alfalah Investments. You provide accurate and polite information regarding our mutual funds, policies, and services.",
    }

    jsonl_lines = []
    # Split text into manageable chunks (e.g., by sentences or paragraphs)
    # This is a naive chunking for demonstration purposes
    chunks = [text[i : i + 500] for i in range(0, len(text), 500)]

    for chunk in chunks:
        # In a real scenario, you'd want user questions paired with assistant answers.
        # Here we just inject the knowledge into the assistant's context.
        user_message = {
            "role": "user",
            "content": "Tell me about Alfalah Investments policies or general information.",
        }
        assistant_message = {"role": "assistant", "content": chunk}

        entry = {"messages": [system_message, user_message, assistant_message]}
        jsonl_lines.append(json.dumps(entry))

    return "\n".join(jsonl_lines)


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )

    try:
        # 1. Download raw file
        response = s3.get_object(Bucket=bucket, Key=key)
        raw_text = response["Body"].read().decode("utf-8")
        print(f"Downloaded {key} from {bucket}")

        # 2. Clean and Process
        cleaned_text = process_text(raw_text)
        print("Text cleaned successfully")

        # 3. Format to JSONL
        jsonl_data = convert_to_jsonl(cleaned_text)

        # 4. Upload to cleaned/ prefix
        # key format: raw/filename.txt -> cleaned/filename.jsonl
        filename = os.path.basename(key)
        name, _ = os.path.splitext(filename)
        cleaned_key = f"cleaned/{name}.jsonl"

        s3.put_object(
            Bucket=bucket,
            Key=cleaned_key,
            Body=jsonl_data.encode("utf-8"),
            ContentType="application/jsonlines",
        )
        print(f"Successfully uploaded processed file to {cleaned_key}")

        return {"statusCode": 200, "body": json.dumps(f"Successfully processed {key}")}

    except Exception as e:
        print(e)
        print(f"Error getting object {key} from bucket {bucket}.")
        raise e
