import logging

from aiobotocore.session import get_session
import botocore.exceptions as exc

from app.settings import settings


class CloudService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bucket = settings.S3_BUCKET
        self.ctx = None

    async def session(self):
        session = get_session()
        client = session.create_client(
            "s3", region_name=settings.S3_REGION_NAME,
            endpoint_url=settings.S3_URL,
            aws_access_key_id=settings.S3_KEY_ID,
            aws_secret_access_key=settings.S3_ACCESS_KEY,
        )
        self.ctx = await client.__aenter__()

    @staticmethod
    def get_link(key):
        return f"{settings.S3_PUBLIC_URL}/{key}.png"

    async def save_file(self, binary_file: bytes, key: str):
        try:
            await self.ctx.put_object(
                Body=binary_file,
                Bucket=self.bucket,
                Key=key,
            )
        except exc.BotoCoreError as e:
            self.logger.error(e)
            raise Exception(f"Ошибка загрузки файла с ключом {key}")
        finally:
            await self.ctx.__aexit__(None, None, None)


