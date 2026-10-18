"""Secure attachment storage service for HealthAware concern evidence.

Provides:
1. Strict magic-byte file signature validation (JPEG, PNG, WebP).
2. Opaque, unpredictable server-side filename generation (UUID).
3. EXIF and metadata stripping via Pillow.
4. Maximum file size enforcement (5 MB).
5. Storage outside public web root with directory traversal protection.
6. Seamless support for S3-compatible cloud storage (e.g. Neon Object Storage)
   with fallback to local filesystem storage for local development and testing.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import uuid
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

SUPPORTED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Signatures (Magic Bytes)
JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RIFF_SIGNATURE = b"RIFF"
WEBP_SIGNATURE = b"WEBP"


def get_attachment_storage_dir() -> str:
    """Returns the configured attachment storage directory, creating it if needed."""
    storage_dir = os.environ.get("ATTACHMENT_STORAGE_DIR", "./local_storage/attachments")
    os.makedirs(storage_dir, exist_ok=True)
    return os.path.abspath(storage_dir)


def detect_image_format(data: bytes) -> Optional[str]:
    """Inspects magic bytes of data buffer to detect image MIME type."""
    if len(data) < 12:
        return None
    if data.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    if data.startswith(RIFF_SIGNATURE) and data[8:12] == WEBP_SIGNATURE:
        return "image/webp"
    return None


def sanitize_and_strip_metadata(data: bytes, detected_format: str) -> bytes:
    """Uses Pillow to verify image validity and strip EXIF and sensitive metadata."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            # Verify file integrity
            img.verify()

        # Re-open for clean re-encoding without EXIF
        with Image.open(io.BytesIO(data)) as img:
            output = io.BytesIO()
            fmt = img.format or ("JPEG" if detected_format == "image/jpeg" else "PNG")
            
            # If RGBA and saving as JPEG, convert to RGB
            if fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            
            # Save clean image without original exif or comments
            img.save(output, format=fmt)
            return output.getvalue()
    except Exception as exc:
        logger.warning("Failed to sanitize image metadata via Pillow: %s", exc)
        raise ValueError("Invalid, corrupted, or unsupported image content.")


class AttachmentStorageService:
    """Storage abstraction for private photo evidence.
    
    Supports local filesystem storage and S3-compatible cloud object storage
    (such as Neon Object Storage) via boto3.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        app_env = os.environ.get("APP_ENV", "").strip().lower()
        self.backend_type = os.environ.get("ATTACHMENT_STORAGE_BACKEND", "local").strip().lower()
        self.storage_dir = storage_dir or get_attachment_storage_dir()
        self.s3_client = None
        self.s3_bucket = os.environ.get("S3_BUCKET_NAME", "").strip()

        if app_env == "production":
            if self.backend_type != "s3":
                raise RuntimeError(
                    "Production configuration error: ATTACHMENT_STORAGE_BACKEND must be set to 's3' when APP_ENV=production. "
                    "Local disk storage is prohibited in production."
                )
            if not self.s3_bucket:
                raise RuntimeError(
                    "Production configuration error: S3_BUCKET_NAME must be configured when APP_ENV=production. "
                    "Silent fallback to local disk is prohibited."
                )
            try:
                import boto3
                endpoint_url = os.environ.get("S3_ENDPOINT_URL")
                aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
                aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
                region = os.environ.get("AWS_REGION", "us-east-2")

                kwargs = {"region_name": region}
                if endpoint_url:
                    kwargs["endpoint_url"] = endpoint_url
                if aws_access_key and aws_secret_key:
                    kwargs["aws_access_key_id"] = aws_access_key
                    kwargs["aws_secret_access_key"] = aws_secret_key

                self.s3_client = boto3.client("s3", **kwargs)
                logger.info("Initialized AttachmentStorageService with S3 backend (bucket: %s)", self.s3_bucket)
            except Exception as e:
                logger.error("Failed to initialize S3 client in production: %s", e)
                raise RuntimeError(f"Production configuration error: Failed to initialize S3 client: {e}")
        else:
            if self.backend_type == "s3":
                try:
                    import boto3
                    endpoint_url = os.environ.get("S3_ENDPOINT_URL")
                    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
                    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
                    region = os.environ.get("AWS_REGION", "us-east-2")

                    kwargs = {"region_name": region}
                    if endpoint_url:
                        kwargs["endpoint_url"] = endpoint_url
                    if aws_access_key and aws_secret_key:
                        kwargs["aws_access_key_id"] = aws_access_key
                        kwargs["aws_secret_access_key"] = aws_secret_key

                    self.s3_client = boto3.client("s3", **kwargs)
                    logger.info("Initialized AttachmentStorageService with S3 backend (bucket: %s)", self.s3_bucket)
                except Exception as e:
                    logger.warning("Failed to initialize S3 client: %s; falling back to local storage.", e)
                    self.backend_type = "local"

    def store_attachment(self, file_bytes: bytes, original_filename: Optional[str] = None) -> Tuple[str, str, int, str]:
        """Validates, strips metadata, and safely persists evidence.
        
        Returns:
            (storage_key, mime_type, file_size_bytes, sha256_checksum)
        """
        if len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum permitted limit of 5 MB ({len(file_bytes)} bytes).")

        mime_type = detect_image_format(file_bytes)
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ValueError("Unsupported file format. Only JPEG, PNG, and WebP images are permitted.")

        # Strip metadata and sanitize
        clean_bytes = sanitize_and_strip_metadata(file_bytes, mime_type)
        checksum = hashlib.sha256(clean_bytes).hexdigest()
        
        ext = SUPPORTED_MIME_TYPES[mime_type]
        storage_key = f"att_{uuid.uuid4().hex}{ext}"

        app_env = os.environ.get("APP_ENV", "").strip().lower()

        if self.backend_type == "s3" and self.s3_client and self.s3_bucket:
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=storage_key,
                    Body=clean_bytes,
                    ContentType=mime_type,
                )
                return storage_key, mime_type, len(clean_bytes), checksum
            except Exception as e:
                logger.error("Failed to store attachment in S3: %s", e)
                raise RuntimeError(f"Cloud storage upload failure: {e}")

        if app_env == "production":
            raise RuntimeError(
                "Production configuration error: S3 attachment storage is required. "
                "Writing complaint evidence to local disk is prohibited in production."
            )

        # Local filesystem persistence for development / testing environments
        target_path = os.path.join(self.storage_dir, storage_key)
        with open(target_path, "wb") as f:
            f.write(clean_bytes)

        return storage_key, mime_type, len(clean_bytes), checksum

    def get_attachment_path(self, storage_key: str) -> Optional[str]:
        """Resolves the absolute path of an attachment file with directory traversal defense.
        
        Note: Only valid for local storage.
        """
        if not storage_key or ".." in storage_key or "/" in storage_key or "\\" in storage_key:
            return None
        
        path = os.path.join(self.storage_dir, storage_key)
        if os.path.exists(path) and os.path.isfile(path):
            return path
        return None

    def read_attachment_bytes(self, storage_key: str) -> Optional[bytes]:
        """Reads the sanitized file bytes for an authorized request."""
        if not storage_key or ".." in storage_key or "/" in storage_key or "\\" in storage_key:
            return None

        if self.backend_type == "s3" and self.s3_client and self.s3_bucket:
            try:
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=storage_key)
                return response["Body"].read()
            except Exception as e:
                logger.warning("Failed to retrieve attachment %s from S3: %s", storage_key, e)
                return None

        app_env = os.environ.get("APP_ENV", "").strip().lower()
        if app_env == "production":
            logger.error("Production configuration error: Local disk attachment read attempted in production.")
            return None

        # Local filesystem read
        path = self.get_attachment_path(storage_key)
        if not path:
            return None
        with open(path, "rb") as f:
            return f.read()
