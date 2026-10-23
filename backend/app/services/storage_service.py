import boto3
import uuid

BUCKET = "skill-barter-images"

s3 = boto3.client("s3")


def upload_file(file_obj, filename):

    key = f"profile_images/{uuid.uuid4()}_{filename}"

    s3.upload_fileobj(file_obj, BUCKET, key)

    return f"https://{BUCKET}.s3.amazonaws.com/{key}"