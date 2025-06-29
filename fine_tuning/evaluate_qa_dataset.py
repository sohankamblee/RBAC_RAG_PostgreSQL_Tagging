import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import jsonlines
from app.rag_engine import generate_answer
import json

from collections import Counter

from app.embedder import embed_query_to_vector
from app.vector_store import chroma_collection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_context(query, user):
    query_embedding = embed_query_to_vector(query)
    filter_dict = {
        "$or": [
            {"access_tags": {"$in": user["access_tags"]}},
            {"roles": {"$in": user["roles"]}}
        ]
    }
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where=filter_dict
    )
    docs = results.get("documents", [[]])[0]
    return "\n".join(docs) if docs else ""

def context_overlap(answer, context):
    answer_tokens = answer.lower().split()
    context_tokens = context.lower().split()
    context_counter = Counter(context_tokens)
    common_tokens = [t for t in answer_tokens if t in context_counter]
    return len(common_tokens) / len(answer_tokens) if answer_tokens else 0

test_user = {
    "roles": ["it_user"],
    "access_tags": ["it_user","it_only", "general_access"],
}

pdf_access = {
    "Data_Visualization_Guidelines.pdf": {
        "roles": ["it_user"],
        "access_tags": ["it_user", "it_only"]
    },
    "Cloud_Usage_Policy.pdf": {
        "roles": ["it_user"],
        "access_tags": ["it_user", "it_only"]
    },
    "Audit_logs_and_Trials.pdf": {
        "roles": ["it_user"],
        "access_tags": ["it_user", "it_only"]
    },
    "Performance_Review_Policy_ACME.pdf": {
        "roles": ["hr_user"],
        "access_tags": ["hr_only","hr_user"]
    },
    "Recruitment_Guidelines_ACME.pdf": {
        "roles": ["hr_user"],
        "access_tags": ["hr_only","hr_user"]
    },
    "Internship_Policy_expanded.pdf": {
        "roles": ["hr_user"],
        "access_tags": ["hr_only","hr_user"]
    },
    "Email_Etiquette_and_Collaboration_Tool_Usage.pdf": {
        "roles": ["general_access", "it_user", "hr_user"],
        "access_tags": ["general_access"]
    },
    "Long_Leave_of_Absence_Policy_ACME.pdf": {
        "roles": ["general_access", "hr_user", "it_user"],
        "access_tags": ["general_access"]
    },
    "Dress_Code_Guidelines_ACME.pdf": {
        "roles": ["general_access", "hr_user", "it_user"],
        "access_tags": ["general_access"]
    },
    "Employee_Referral_Policy_ACME.pdf": {
        "roles": ["general_access", "hr_user", "it_user"],
        "access_tags": ["general_access"]
    }
}

async def evaluate_model():
    total = 0
    correct = 0
    mismatches = []
    skipped = 0

    logger.info("Starting QA evaluation...")
    with jsonlines.open("qa_dataset.jsonl") as reader:
        for idx, item in enumerate(reader):
            query = item["prompt"]
            expected = item["completion"]
            source_pdf = item.get("source_pdf")
            logger.info(f"Processing QA {idx+1}: {query[:60]}... (source: {source_pdf})")

            # --- Filter: Only evaluate if user has access to this PDF ---
            access = pdf_access.get(source_pdf)
            if not access:
                logger.warning(f"Skipping {source_pdf}: no access metadata found.")
                skipped += 1
                continue

            user_has_access = (
                bool(set(test_user["roles"]) & set(access["roles"])) or
                bool(set(test_user["access_tags"]) & set(access["access_tags"]))
            )
            if not user_has_access:
                logger.info(f"Skipping QA {idx+1}: user lacks access to {source_pdf}")
                skipped += 1
                continue
            # --- End filter ---

            try:
                logger.info(f"Evaluating QA {idx+1}...")
                model_answer = await generate_answer(query, test_user)
                total += 1

                if expected.strip().lower() in model_answer.strip().lower():
                    correct += 1
                    logger.info(f"QA {idx+1}: Correct match.")
                else:
                    mismatches.append({
                        "query": query,
                        "expected": expected,
                        "got": model_answer
                    })
                    logger.info(f"QA {idx+1}: Mismatch.")

                context = get_context(query, test_user)
                score = context_overlap(model_answer, context)
                if score < 0.5:
                    logger.warning(f"QA {idx+1}: Likely hallucination (context overlap < 0.5).")

            except Exception as e:
                logger.error(f"Error for query: {query}\n{e}\n")

    # Summary
    logger.info(f"\nEvaluated {total} QAs (skipped {skipped} due to RBAC)")
    logger.info(f"Correct (approx match): {correct}")
    logger.info(f"Accuracy: {correct / total:.2f}" if total else "Accuracy: N/A")
    logger.info("\n--- Mismatches ---")
    for item in mismatches[:5]:  # Show first 5 mismatches
        logger.info(json.dumps(item, indent=2))

if __name__ == "__main__":
    asyncio.run(evaluate_model())