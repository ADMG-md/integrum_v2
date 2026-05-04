from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from src.services.extraction_service import extraction_service
from src.services.auth_service import check_role
from src.models.user import UserRole, UserModel
import os
import tempfile
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/upload-pdf")
async def upload_lab_pdf(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(
        check_role([UserRole.PHYSICIAN, UserRole.SUPERADMIN])
    ),
):
    """
    Receives a PDF laboratory report and returns extracted observations.
    HIPAA/Habeas Data compliant: all PII is scrubbed before processing.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Validate MIME type
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF allowed."
        )

    # Max 10MB
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = extraction_service.extract_from_pdf(tmp_path)
        return result
    except Exception as e:
        # SEC-04: log internally, never expose internal extraction errors to client
        import structlog
        structlog.get_logger().error("pdf_extraction_error", filename=file.filename, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Error processing PDF. Verify the file is a valid lab report.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
