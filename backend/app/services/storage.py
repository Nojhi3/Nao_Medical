from __future__ import annotations

import uuid

import boto3

from ..config import settings


class StorageService:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id or None,
            aws_secret_access_key=settings.s3_secret_access_key or None,
        )

    def presign_audio_upload(self, conversation_id: str, mime_type: str) -> dict[str, str]:
        ext = "webm"
        key = f"conversations/{conversation_id}/{uuid.uuid4()}.{ext}"
        upload_url = self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": key,
                "ContentType": mime_type,
            },
            ExpiresIn=600,
        )

        if settings.s3_public_base_url:
            base = settings.s3_public_base_url.rstrip("/")
            file_url = f"{base}/{key}"
        else:
            endpoint = (settings.s3_endpoint_url or "").rstrip("/")
            file_url = f"{endpoint}/{settings.s3_bucket}/{key}" if endpoint else key

        return {"upload_url": upload_url, "file_url": file_url, "object_key": key}
