"""
S3 / MinIO backed StorageService.
Kept dependency-free by default (boto3 import happens lazily) so the base
project runs without extra installs until S3 is actually enabled.
"""
from typing import BinaryIO

from app.storage.base import StorageService


class S3Storage(StorageService):
    def __init__(self, bucket: str, endpoint_url: str | None = None):
        import boto3  # imported lazily; add boto3 to requirements when enabling S3

        self.bucket = bucket
        self.client = boto3.client("s3", endpoint_url=endpoint_url)

    def save(self, key: str, file_obj: BinaryIO) -> str:
        self.client.upload_fileobj(file_obj, self.bucket, key)
        return key

    def open(self, key: str) -> BinaryIO:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"]

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
