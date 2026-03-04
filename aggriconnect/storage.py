from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'

class MediaStorage(S3Boto3Storage):
    location = 'photos'
    default_acl = 'public-read'
    file_overwrite = False # Prevents two users uploading "farm.jpg" from overwriting each other