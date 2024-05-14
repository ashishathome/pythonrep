import io
import os
from datetime import datetime, timedelta, date
from google.cloud import bigquery
import traceback
import paramiko
from impl.gcs_processor import GCSProcessor
from impl.MessageLogger import MessageLogger
import LogMessage

project_id = os.environ.get("project_id", None)
environment = os.environ.get("environment", None)
function_name = os.environ.get('K_SERVICE', 'Not set')
function_region = os.environ.get('region', 'Not set')
flow_id = os.environ.get('flow_id', 'Not set')
msg_name = os.environ.get('DATA_PIPELINE_LOGGER_NAME', 'Not set')
logger = MessageLogger(instance_id='test_logger', project=project_id, logger_name='test_logger')
alert_id = ""


class SFTPProcessor(object):
    """
    class docs
    """

    def process_files(self, connection, sftp_host, sftp_username, sftp_password, sftp_port, sftp_default_folder_path,
                      prefix, suffix, bucket_name, acquirer, dataset,table_name,business_key,biz_key_val):
        global alert_id
        # to avoid error "AttributeError: 'Connection' object has no attribute '_sftp_live'"
        days_added = timedelta(days = 14)
        d1 = (datetime.today()).strftime('%Y%m%d%H%M%S')
        d2 = (datetime.today() - days_added).strftime('%Y%m%d%H%M%S')
        ssh = paramiko.SSHClient()

        try:
            if connection == "ppk":
                with open("/tmp/ppk.pem", "w") as file:
                    file.write(sftp_password)
                key = paramiko.RSAKey.from_private_key_file("/tmp/ppk.pem")
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(sftp_host, username=sftp_username, port=sftp_port, look_for_keys=False, pkey=key, disabled_algorithms=dict(pubkeys=["rsa-sha2-512", "rsa-sha2-256"]))
            else:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(sftp_host, username=sftp_username, port=sftp_port, look_for_keys=False, password=sftp_password)
            LogMessage.create_message(project_id,function_name,function_region,flow_id,msg_name,'Connection succesfully established with remote SFTP server... ', "INFO", '', '', business_key, biz_key_val)
            sftp = ssh.open_sftp()
            folders = sftp_default_folder_path
            directories = folders.split(",")
            #print(directories)
            listed_files = []
            processed_files = get_processed_files(acquirer,dataset,table_name)
            for directory in directories:
                files_list = sftp.listdir_attr(directory)
                for file in files_list:
                    self.generate_files_list(acquirer, prefix, suffix, business_key, biz_key_val, d1, d2, file, listed_files, directory, processed_files)
            for file in listed_files:
                self.process_files_list(bucket_name, acquirer, prefix, suffix, dataset, table_name, business_key, biz_key_val, file, sftp)
            ssh.close()
            # connection closed automatically at the end of the with-block
            LogMessage.create_message(project_id,function_name,function_region,flow_id,msg_name,'Connection with remote SFTP was closed. ', "INFO", '', '', business_key, biz_key_val)
        except FileNotFoundError as e3:
            LogMessage.create_message(project_id,function_name,function_region,flow_id,msg_name,'The remote sftp path does not exist', "ERROR", 'SFTP-003', str(e3), business_key, biz_key_val)
            raise
        except paramiko.AuthenticationException as e4:
            LogMessage.create_message(project_id, function_name, function_region, flow_id, msg_name, 'Authentication error', "ERROR", "SFTP-002", str(e4), business_key, biz_key_val)
            raise
        except Exception as e:
            traceback.print_exc()
            if alert_id == "":
                alert_id="ERR-001"
                error_reason = "Unhandled error"
            LogMessage.create_message(project_id, function_name, function_region, flow_id, msg_name, '{} in sftp_proccessor for acquirer {}'.format(error_reason,acquirer), "ERROR", alert_id, str(e), business_key, biz_key_val)
            raise

    def process_files_list(self, bucket_name, acquirer, prefix, suffix, dataset, table_name, business_key, biz_key_val, file, sftp):
        gcs_uploader = GCSProcessor()
        file_content = io.BytesIO()

        #bnpp have to kind of files xml and fixed format(frfc).
        if acquirer == 'bnpp':
            filename = file.split('/')[-1]
            if len(filename) > 7:
                if filename [:7] == 'SFPA0GY':
                    filename = filename + '.xml'
                elif filename [:7] == 'SFPA0TU': 
                    filename = filename + '.frfc'

        #postfinance have to kind of files xml (online & store)
        if acquirer == 'postfinance':
            filename = file.split('/')[-1] + '.xml' if 'TK5080540000000' in file else file.split('/')[-1]
                    
        else:
            if prefix is not None:
                filename = prefix + file.split('/')[-1]
            elif suffix is not None:
                filename = file.split('/')[-1] + suffix
            else:
                filename = file.split('/')[-1]
            
        attr = sftp.stat(file)
        sftp.getfo(file,file_content)
        print("file size {}".format(str(attr.st_size)))     

        gcs_uploader.upload_file_to_gcs_bucket(filename, file_content, bucket_name,function_name, function_region,flow_id,msg_name,business_key,biz_key_val)
        load_data_bigquery(project_id, dataset, table_name, acquirer, filename)
        LogMessage.create_message(project_id,function_name,function_region,flow_id,msg_name,"File " + filename + " successfully processed", "INFO", '', '', business_key, biz_key_val)

    def generate_files_list(self, acquirer, prefix, suffix, business_key, biz_key_val, d1, d2, file, listed_files, directory, processed_files):
        file_date = (datetime.fromtimestamp(file.st_mtime)).strftime('%Y%m%d%H%M%S')
        if file_date >= d2 and file_date < d1:
                 
            #bnpp have to kind of files xml and fixed format(frfc).
            if acquirer == 'bnpp':
                filename_chk = file.filename
                if len(filename_chk) > 7:
                    if filename_chk [:7] == 'SFPA0GY':
                        filename_chk = filename_chk + '.xml'
                    elif filename_chk [:7] == 'SFPA0TU': 
                        filename_chk = filename_chk + '.frfc'
                 
            #postfinance have to kind of files xml (online & store)
            if acquirer == 'postfinance':
                filename_chk = file.filename + '.xml' if 'TK5080540000000' in file.filename else file.filename
                          
            else:
                if prefix is not None:
                    filename_chk = prefix + file.filename          
                elif suffix is not None:
                    filename_chk = file.filename + suffix   
                else:
                    filename_chk = file.filename
            
            if filename_chk not in processed_files:
                file_path = directory + file.filename
                if file_path not in listed_files:
                    listed_files.append(file_path)
            else:
                LogMessage.create_message(project_id,function_name,function_region,flow_id,msg_name,"File " + file.filename + " already processed, skipping", "INFO", '', '', business_key, biz_key_val)


def load_data_bigquery(project_id, dataset_id, table_name, acquirer, file_name):
    data = {}
    data['LoadDate'] = str(date.today())
    data['Acquirer'] = acquirer
    data['FileName'] = file_name
    data['ProcessedTimestamp'] = str(datetime.utcnow())
    print(data)
    data_to_load = []
    try:
        data_to_load.append(data)
        client = bigquery.Client()
        dataset_ref = client.dataset(dataset_id, project_id)
        table = client.get_table(dataset_ref.table(table_name))
        errors = client.insert_rows_json(table, data_to_load)  # API request
        if errors == []:
            print("New rows have been added to BQ.")
        else:
            LogMessage.create_message(project_id, function_name, function_region, flow_id, msg_name, "Encountered errors while inserting rows: {}".format(errors), "ERROR", 'BQ-001' , '', "", "")    
    except Exception as e:
        global error_reason
        error_reason = "Error loggin file in bigquery table"
        global alert_id
        alert_id = "BQ-001"
        raise e


def get_processed_files(acquirer,dataset_id,table_name):
    try:
        client = bigquery.Client()
        job_config = bigquery.QueryJobConfig(use_query_cache=False)

        #Check the files processed in the last 30 daýs.
        days_from = 30
        date_from  = date.today() - timedelta(days_from)
        query_job_dates = client.query(
        (
            "SELECT FileName FROM " + project_id + "." + dataset_id + "." + table_name + " WHERE LoadDate >= '" + str(date_from) + "' AND Acquirer = '" + acquirer + "'"
        ),
        job_config=job_config,
        )
        file_list = []
        for row in query_job_dates:
            file_in_table = row["FileName"]
            file_list.append(file_in_table)
        return file_list
    except Exception as e:
        global error_reason
        error_reason = "Error checking in BQ table if the file was proccessed"
        raise e
    