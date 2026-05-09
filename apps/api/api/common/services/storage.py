# =============================================================================
# 모듈 설명: MinIO(S3 호환) 오브젝트 스토리지 접근 유틸을 제공합니다.
# - 주요 함수: get_minio_client, ensure_minio_bucket, upload_bytes, download_bytes, delete_object
# - 불변 조건: 버킷 이름은 settings.MINIO_BUCKET 값을 사용합니다.
# =============================================================================

from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

# =============================================================================
# 로깅
# =============================================================================
logger = logging.getLogger(__name__)

# =============================================================================
# 모듈 상태
# =============================================================================
_MINIO_CLIENT: Any | None = None
_BUCKET_READY = False
_MISSING_BUCKET_ERROR_CODES = {"404", "NoSuchBucket"}
_MISSING_OBJECT_ERROR_CODES = {"404", "NoSuchBucket", "NoSuchKey"}


def _client_error_code(exc: ClientError) -> str:
    """botocore ClientError에서 에러 코드를 안전하게 추출합니다."""

    return str(exc.response.get("Error", {}).get("Code", ""))


def _is_client_error_code(exc: ClientError, codes: set[str]) -> bool:
    """ClientError가 지정된 S3/MinIO 에러 코드에 해당하는지 확인합니다."""

    return _client_error_code(exc) in codes


def _build_minio_client() -> Any:
    """MinIO(S3 호환) 클라이언트를 생성합니다.

    입력:
        없음(settings에서 설정값 사용).
    반환:
        boto3 S3 클라이언트.
    부작용:
        없음.
    오류:
        설정값이 비어 있으면 예외가 발생할 수 있음.
    """

    # -----------------------------------------------------------------------------
    # 1) 설정값 준비
    # -----------------------------------------------------------------------------
    endpoint = getattr(settings, "MINIO_ENDPOINT", "") or ""
    access_key = getattr(settings, "MINIO_ACCESS_KEY", "") or ""
    secret_key = getattr(settings, "MINIO_SECRET_KEY", "") or ""
    region = getattr(settings, "MINIO_REGION", "") or None

    # -----------------------------------------------------------------------------
    # 2) 클라이언트 생성
    # -----------------------------------------------------------------------------
    config = Config(signature_version="s3v4", s3={"addressing_style": "path"})
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=config,
    )


def get_minio_client() -> Any:
    """MinIO(S3 호환) 클라이언트를 반환합니다(싱글턴 캐시).

    입력:
        없음.
    반환:
        boto3 S3 클라이언트.
    부작용:
        최초 호출 시 클라이언트 생성.
    오류:
        클라이언트 생성 실패 시 예외 발생.
    """

    # -----------------------------------------------------------------------------
    # 1) 캐시 확인 및 생성
    # -----------------------------------------------------------------------------
    global _MINIO_CLIENT
    if _MINIO_CLIENT is None:
        _MINIO_CLIENT = _build_minio_client()
    return _MINIO_CLIENT


def ensure_minio_bucket() -> str:
    """MinIO 버킷 존재를 보장하고 버킷 이름을 반환합니다.

    입력:
        없음(settings에서 버킷 이름 사용).
    반환:
        버킷 이름 문자열.
    부작용:
        버킷이 없으면 생성할 수 있음.
    오류:
        MinIO 오류가 발생할 수 있음.
    """

    # -----------------------------------------------------------------------------
    # 1) 캐시 확인
    # -----------------------------------------------------------------------------
    global _BUCKET_READY
    if _BUCKET_READY:
        return settings.MINIO_BUCKET

    # -----------------------------------------------------------------------------
    # 2) 버킷 존재 여부 확인
    # -----------------------------------------------------------------------------
    client = get_minio_client()
    bucket = settings.MINIO_BUCKET
    if not bucket:
        raise ValueError("MINIO_BUCKET is not configured")
    try:
        client.head_bucket(Bucket=bucket)
        _BUCKET_READY = True
        return bucket
    except ClientError as exc:
        if not _is_client_error_code(exc, _MISSING_BUCKET_ERROR_CODES):
            raise

    # -----------------------------------------------------------------------------
    # 3) 버킷 생성
    # -----------------------------------------------------------------------------
    region = getattr(settings, "MINIO_REGION", "") or ""
    try:
        if region and region != "us-east-1":
            client.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region})
        else:
            client.create_bucket(Bucket=bucket)
    except ClientError:
        logger.exception("Failed to create MinIO bucket: %s", bucket)
        raise

    _BUCKET_READY = True
    return bucket


def upload_bytes(*, object_key: str, data: bytes, content_type: str | None = None) -> None:
    """바이트 데이터를 MinIO에 업로드합니다.

    입력:
        object_key: 저장할 오브젝트 키.
        data: 업로드할 바이트 데이터.
        content_type: Content-Type(옵션).
    반환:
        없음.
    부작용:
        MinIO에 오브젝트 저장.
    오류:
        MinIO 오류가 발생할 수 있음.
    """

    # -----------------------------------------------------------------------------
    # 1) 버킷/클라이언트 준비
    # -----------------------------------------------------------------------------
    bucket = ensure_minio_bucket()
    client = get_minio_client()
    resolved_type = content_type or "application/octet-stream"

    # -----------------------------------------------------------------------------
    # 2) 업로드 수행
    # -----------------------------------------------------------------------------
    client.put_object(Bucket=bucket, Key=object_key, Body=data, ContentType=resolved_type)


def download_bytes(*, object_key: str) -> bytes | None:
    """MinIO에서 오브젝트를 다운로드해 바이트로 반환합니다.

    입력:
        object_key: 오브젝트 키.
    반환:
        바이트 데이터 또는 None(없을 때).
    부작용:
        MinIO에 GET 요청 발생.
    오류:
        MinIO 오류가 발생할 수 있음.
    """

    # -----------------------------------------------------------------------------
    # 1) 버킷/클라이언트 준비
    # -----------------------------------------------------------------------------
    bucket = ensure_minio_bucket()
    client = get_minio_client()

    # -----------------------------------------------------------------------------
    # 2) 오브젝트 다운로드
    # -----------------------------------------------------------------------------
    try:
        response = client.get_object(Bucket=bucket, Key=object_key)
    except ClientError as exc:
        if _is_client_error_code(exc, _MISSING_OBJECT_ERROR_CODES):
            return None
        raise

    body = response.get("Body")
    if body is None:
        return None
    try:
        return body.read()
    finally:
        try:
            body.close()
        except Exception:
            pass


def delete_object(*, object_key: str) -> None:
    """MinIO 오브젝트를 삭제합니다(없어도 성공 처리).

    입력:
        object_key: 오브젝트 키.
    반환:
        없음.
    부작용:
        MinIO에 DELETE 요청 발생.
    오류:
        MinIO 오류가 발생할 수 있음.
    """

    # -----------------------------------------------------------------------------
    # 1) 버킷/클라이언트 준비
    # -----------------------------------------------------------------------------
    bucket = ensure_minio_bucket()
    client = get_minio_client()

    # -----------------------------------------------------------------------------
    # 2) 삭제 수행
    # -----------------------------------------------------------------------------
    try:
        client.delete_object(Bucket=bucket, Key=object_key)
    except ClientError as exc:
        if _is_client_error_code(exc, _MISSING_OBJECT_ERROR_CODES):
            return
        raise


__all__ = ["delete_object", "download_bytes", "ensure_minio_bucket", "get_minio_client", "upload_bytes"]
