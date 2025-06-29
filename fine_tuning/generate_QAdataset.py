import subprocess
import json
import re

def generate_qa_ollama(chunk, role):
    prompt = f"""
    You are a professional document analyst creating training data for a retrieval-based chatbot.

    Given the following document excerpt, extract a **high-quality, factual, role-specific** question and its corresponding answer.

    Only use information directly present in the document — do not infer or assume.
    Be specific. Avoid vague or general questions.
    Prefer to include details like emails, policies, job titles, procedures, or numerical facts.

    Document (for role: {role}):
    \"\"\"
    {chunk}
    \"\"\"

    Return your output in valid JSON format as:
    {{"prompt": "<question>", "completion": "<answer>"}}
    """

    
    command = ["ollama", "run", "mistral", prompt]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    
    try:
        output = result.stdout.strip()
        # Extract JSON object from output
        match = re.search(r'\{.*\}', output, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            print("No JSON found in output:", output)
            return None
    except Exception as e:
        print("Error parsing:", output)
        return None
