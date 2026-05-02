# Alfalah GPT — Data Gathering & Preprocessing Guide

This document outlines exactly **what** data needs to be gathered and **how** it should be processed for both the RAG (Retrieval-Augmented Generation) pipeline and the OpenAI Fine-Tuning pipeline.

---

## 1. RAG (Retrieval-Augmented Generation) Data

RAG is used for facts, policies, and dense institutional knowledge. The LLM retrieves this context at runtime to avoid hallucinating specific fund rules.

### What Data to Gather?
- **Fund Prospectuses (Offering Documents):** Contains the official investment objective, risk profile, benchmark, and asset allocation limits for every fund.
- **Fund Manager Reports (FMR):** Monthly PDFs detailing the fund's top holdings, sector allocations, and market commentary.
- **Trust Deeds:** Legal definitions and fee structures (management fees, front-end loads).
- **SECP Regulations:** Non-Banking Finance Companies (NBFC) regulations and Shariah compliance fatwas relevant to Alfalah AMC.

### How to Gather & Process It
1. **Download (Scraping):**
   - Use the `knowledge_base/scripts/seed.py` script to automate downloading PDFs from `https://www.alfalahamc.com/downloads/`.
2. **Text Extraction:**
   - Use `PyMuPDF` or `pdfplumber` to extract raw text from the downloaded PDFs.
3. **Chunking & Metadata:**
   - Text must be split into chunks of ~500-1000 tokens using a tool like LangChain's `RecursiveCharacterTextSplitter`.
   - **Crucial:** Attach metadata to every chunk (e.g., `{"fund_name": "Alfalah GHP Islamic Income Fund", "doc_type": "FMR", "date": "2026-02"}`). This allows the RAG tool to filter by fund name before performing semantic search.
4. **Embedding & Storage:**
   - Pass chunks through `sentence-transformers/all-MiniLM-L6-v2`.
   - Upsert the vectors and metadata into the **ChromaDB** vector store.

---

## 2. OpenAI Fine-Tuning Data

Fine-tuning is *not* used for memorizing facts (like NAV or specific fees). Instead, it is used to teach the model **tone, personality, formatting, and behavioral flows** (e.g., how to politely escalate to a human, or how to phrase financial disclaimers).

### What Data to Gather?
- **Tone & Style Guides:** "Alfalah brand guidelines" on how to speak to clients (e.g., professional, empathetic, clear).
- **FAQ Pairs:** Hundreds of examples of common customer queries and the *exact* way a perfect human agent would reply.
- **Routing & Tool Calling Examples:** Examples teaching the LLM *when* to trigger `search_kb` vs `get_fund_nav`.
- **Disclaimer Injection:** Examples showing the LLM appending "Past performance is not indicative of future returns" when discussing fund performance.

### How to Gather & Process It
1. **Upload Raw Text via Admin Panel:**
   - An admin uploads text files or CSVs containing FAQs/guidelines through the `knowledge_base.html` admin UI.
   - The backend uploads these to the AWS S3 Bucket under the `raw/` prefix.
2. **Lambda Preprocessing:**
   - An AWS Lambda function is automatically triggered by the S3 upload.
   - The Lambda script removes unnecessary whitespace, filters out generic legal boilerplate (to save tokens), and restructures the data.
3. **JSONL Formatting:**
   - The Lambda function formats the data into OpenAI's strict Chat Completion JSONL format.
   - Every line in the `.jsonl` file must represent a full conversation.
   - **Example format required:**
     ```json
     {"messages": [{"role": "system", "content": "You are Alfalah GPT, a helpful financial assistant."}, {"role": "user", "content": "How do I open an account?"}, {"role": "assistant", "content": "To open an account with Alfalah Investments, you can download our app..."}]}
     ```
4. **Output & Training:**
   - The Lambda script saves the formatted file to the `cleaned/` prefix in S3.
   - The Admin can then click "Trigger Fine-Tuning" in the LLMOps dashboard, which invokes `finetuning_service.py` to send the `cleaned.jsonl` file to the OpenAI API.

---

## Summary of Data Split
| Data Type | Best Pipeline | Why? |
|-----------|--------------|------|
| Fund NAVs & Returns | **Live Web Scraping** | Changes daily; cannot be stored in RAG or FT. |
| Prospectuses / Legal PDFs | **RAG (ChromaDB)** | Too large to fine-tune; needs exact text retrieval. |
| Chat Tone / Agent Behavior | **Fine-Tuning (OpenAI)** | Teaches the model *how* to talk and *when* to use tools. |
