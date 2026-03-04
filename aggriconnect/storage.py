from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    location = 'static'

class MediaStorage(S3Boto3Storage):
    location = 'photos'
    file_overwrite = False # Prevents two users uploading "farm.jpg" from overwriting each other