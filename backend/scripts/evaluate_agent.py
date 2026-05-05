"""
LLMOps Evaluation Engine
=========================
Runs the agent against `tests/eval/golden_dataset.json` and checks if the correct
tool was selected by the LLM for each test case.
Metrics logged: Tool Calling Accuracy (%).
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI

from app.agent.tool_registry import OPENAI_TOOLS


def run_evaluation() -> None:
    print("Running LLMOps Tool Evaluation...")

    # We skip actual eval if OPENAI_API_KEY is not genuinely set (e.g., in basic PR linting)
    # We only want this to run when there's a valid key, or we mock it.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-test-placeholder":  # pragma: allowlist secret
        print("⚠️ OPENAI_API_KEY is missing or placeholder. Skipping actual OpenAI LLM evaluation.")
        print("✅ Tool Evaluation PASSED (Skipped).")
        sys.exit(0)

    dataset_path = Path(__file__).parent.parent / "tests" / "eval" / "golden_dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    client = OpenAI()
    correct = 0
    total = len(dataset)

    print(f"Loaded {total} test cases.")

    for i, test in enumerate(dataset):
        query = test["input"]
        expected_tool = test["expected_tool"]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": query}],
            tools=OPENAI_TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        actual_tool = None
        if msg.tool_calls:
            actual_tool = msg.tool_calls[0].function.name

        if actual_tool == expected_tool:
            correct += 1
            print(f"  [{i + 1}/{total}] ✅ PASS | Expected: {expected_tool} | Got: {actual_tool}")
        else:
            print(f"  [{i + 1}/{total}] ❌ FAIL | Expected: {expected_tool} | Got: {actual_tool} | Query: {query}")

    accuracy = (correct / total) * 100
    print("\n--- Evaluation Complete ---")
    print(f"Accuracy: {accuracy}% ({correct}/{total})")

    if accuracy < 90.0:
        print("❌ Accuracy below 90% threshold. Failing CI.")
        sys.exit(1)

    print("✅ Accuracy meets threshold.")
    sys.exit(0)


if __name__ == "__main__":
    run_evaluation()
