# tagging_test_main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import tempfile
import os
import asyncio
import uvicorn
import logging
from app.auto_tagging import extract_pdf_text, build_prompt, call_ollama

app = FastAPI()



@app.post("/upload/")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)    
    
    if not files:
        return JSONResponse(content={"error": "No files uploaded"}, status_code=400)
    logger.info(f"Received {len(files)} files for processing.")
    
    results = {}

    for file in files:
        try:
            suffix = os.path.splitext(file.filename)[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            text = extract_pdf_text(tmp_path)
            logger.info(f"Extracted text from {file.filename}, length: {len(text)}")
            
            prompt = build_prompt(text)
            logger.info(f"Built prompt for {file.filename}")
            
            tags = await call_ollama(prompt)
            logger.info(f"Received tags for {file.filename}: {tags}")

            results[file.filename] = tags

            os.unlink(tmp_path)

        except Exception as e:
            results[file.filename] = {"error": str(e)}
            logger.error(f"Error processing {file.filename}: {e}")
    logger.info("Processing complete.")
    return JSONResponse(content=results)
       
if __name__ == "__main__":
    uvicorn.run("tagging_test_main:app", host="127.0.0.1", port=8000, reload=True)
