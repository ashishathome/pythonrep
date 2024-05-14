import os
import json
import traceback
from impl.sftp_processor import SFTPProcessor
import LogMessage
from google.cloud import secretmanager
import functions_framework


PROJECT_ID = os.environ.get("project_id", None)
SFTP_SECRET = os.environ.get("sftp_secret", None)
GCS_BUCKET_NAME = os.environ.get('gcs_bucket_name', None)
ACQUIRER = os.environ.get('acquirer', None)
CONNECTION = os.environ.get('connection', None)
DATASET = os.environ.get('dataset')
TABLE_NAME = os.environ.get('table_name')
function_name = os.environ.get('K_SERVICE', 'Not set')
function_region = os.environ.get('region', 'Not set')
flow_id = os.environ.get('flow_id', 'Not set')
msg_name = os.environ.get('DATA_PIPELINE_LOGGER_NAME', 'Not set')
business_key = ''
biz_key_val = 'NA'
alert_id = ""
error_reason = ""
alert_id = ""


@functions_framework.http
def start_execution(request):
    global alert_id
    try:
        sftp_processor = SFTPProcessor()
        # get credentials from secret 
        creds = get_api_credentials(PROJECT_ID, SFTP_SECRET)

        for credentials in creds: 
            prefix = credentials['prefix'] if "prefix" in credentials else None   
            suffix = credentials['suffix'] if "suffix" in credentials else None       
            
                
            username = credentials['user']
            password = credentials['password']
            host = credentials['host']
            port = credentials['port']
            sftp_directory = credentials['directory']
            if CONNECTION == "ppk":
                sftp_password = get_api_credentials(PROJECT_ID, password)
            else:
                sftp_password = password
            print("username: {}".format(username))
            print("host: {}".format(host))
            print("port: {}".format(port))
            print("sftp directory: {}".format(sftp_directory))
            sftp_processor.process_files(CONNECTION, host, username , sftp_password, 
                                         port, sftp_directory, prefix, suffix, GCS_BUCKET_NAME,
                                         ACQUIRER, DATASET, TABLE_NAME, 
                                         business_key , biz_key_val)
        return "200"
    except ValueError as e4:
        traceback.print_exc()
        alert_id = "ERR-001"
        LogMessage.create_message(PROJECT_ID, function_name, function_region, flow_id, 
                                  msg_name, 'Invalid parameters', "ERROR", 
                                  alert_id, str(e4), business_key, biz_key_val)
        return "500"
    
    except Exception as e5:
        traceback.print_exc()
        if alert_id == "":
            alert_id = "ERR-001"
            error_reason = 'Unhandled error'
        LogMessage.create_message(PROJECT_ID, function_name, function_region, flow_id, 
                                  msg_name, error_reason, "ERROR", 
                                  alert_id, str(e5), business_key, biz_key_val)
        return "500"

def get_api_credentials(PROJECT_ID, API_SECRET):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{API_SECRET}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        if payload.startswith("{") or payload.startswith("[") : 
            creds = json.loads(payload)
        else:
            creds = payload
        return creds
    except CredentialsError as e:
        alert_id = 'AUTH-001'
        LogMessage.create_message(PROJECT_ID, function_name, function_region, 
                                  flow_id, msg_name, 'Error retrieving endpoint '
                                  + 'username  and password from Secrets', "ERROR", 
                                  alert_id, str(e), business_key, biz_key_val)
        raise CredentialsError

class CredentialsError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'CredentialsError, {0} '.format(self.message)
        else:
            return 'CredentialsError has been raised'
