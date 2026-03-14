from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import uuid
import shutil
from database.firestore import get_db

router = APIRouter(prefix="/api/upload", tags=["Upload"])

@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Form(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    doc_id = str(uuid.uuid4())
    temp_file_path = f"temp_{doc_id}.pdf"
    
    try:
        from rag.ingest import ingest_pdf
        from services.topic_outline_generator import generate_topic_outline

        print(f"Starting PDF upload for user: {user_id}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print("Ingesting PDF chunks...")
        chunks = ingest_pdf(temp_file_path, doc_id, user_id)
        print(f"Generated {chunks} chunks. Generating topic outline...")
        topic_outline = generate_topic_outline(doc_id)
        
        db = get_db()
        if db:
            print("Saving to Firestore...")
            db.collection("documents").document(doc_id).set({
                "doc_id": doc_id,
                "user_id": user_id,
                "title": file.filename,
                "type": "pdf",
                "chunks": chunks,
                "topic_outline": topic_outline
            })
            
        return {
            "message": "PDF uploaded successfully",
            "doc_id": doc_id,
            "title": file.filename,
            "chunks": chunks,
            "topic_outline": topic_outline,
        }
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/url")
async def upload_url(url: str = Form(...), user_id: str = Form(...)):
    try:
        from rag.ingest import ingest_url
        from services.topic_outline_generator import generate_topic_outline

        print(f"Starting URL ingestion for user: {user_id}, URL: {url}")
        doc_id = str(uuid.uuid4())
        
        print("Ingesting URL content...")
        title, chunks = ingest_url(url, doc_id, user_id)
        print(f"Generated {chunks} chunks for '{title}'. Generating topic outline...")
        topic_outline = generate_topic_outline(doc_id)
        
        db = get_db()
        if db:
            print("Saving to Firestore...")
            db.collection("documents").document(doc_id).set({
                "doc_id": doc_id,
                "user_id": user_id,
                "title": title,
                "type": "url",
                "chunks": chunks,
                "topic_outline": topic_outline
            })
            
        return {
            "message": "URL ingested successfully",
            "doc_id": doc_id,
            "title": title,
            "chunks": chunks,
            "topic_outline": topic_outline,
        }
    except Exception as e:
        print(f"URL ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
