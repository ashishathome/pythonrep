import os
from google.cloud import storage
from impl.MessageLogger import MessageLogger

project_id = os.environ.get("project_id", None)
logger = MessageLogger(instance_id='test_logger', project=project_id, logger_name='test_logger')


class GCSProcessor(object):
    """
    class docs
    """

    def upload_file_to_gcs_bucket(self, file_name, file_data, bucket_name,funciton_name, function_region,flow_id,msg_name, business_key,biz_key_val):
        """Uploads a file to the bucket."""
        destination_blob_name = file_name
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_string(file_data.getvalue())
            logger.info("Remote file with name {} uploaded to gcs bucket : {} ...".format(file_name, bucket_name))
        except Exception as e:
            global error_reason
            error_reason = "Error uploading file {} to bucket".format(file_name)
            global alert_id
            alert_id = "GCS-001"
            raise e


    def download_blob_content(self, bucket_name, source_blob_name):
        """Downloads a blob from the bucket."""
        print("downloading credentials from bucket")
        storage_client = storage.Client()
        try:
            bucket = storage_client.get_bucket(bucket_name)
        except:
            raise BucketNotFound
        try:
            blob = bucket.blob(source_blob_name)
            blob_content = blob.download_as_string()
            return blob_content
        except:
            raise BlobNotFound


class BucketNotFound(Exception):
    print("download_blob_content exception1")
    """Raised when the Bucket is not found"""
    pass

class BlobNotFound(Exception):
    print("download_blob_content exception2")
    """Raised when the Blob is not found"""
    pass