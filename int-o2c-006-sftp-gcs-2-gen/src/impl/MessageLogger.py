import logging

from google.cloud import logging_v2 as cloudlogging
from google.cloud.logging_v2.handlers import CloudLoggingHandler

class MessageLogger():

    #def __init__(self, instance_id: str = LOGGER_INSTANCE_ID, instance_zone: str = LOGGER_INSTANCE_ZONE) -> None:
    def __init__(self, instance_id, project, logger_name):
        self.instance_id = instance_id
        self.client = cloudlogging.Client(project = project)
        self.handler = CloudLoggingHandler(self.client)
        self.logger = logging.getLogger(logger_name)
        self.handler.setFormatter(logging.Formatter('%(message)s'))

        if not self.logger.handlers:
            self.logger.addHandler(self.handler)
            self.logger.setLevel(logging.INFO)

    def info(self, log_this):
        self.logger.setLevel(logging.INFO)
        self.logger.info(log_this)

    def warning(self, log_this):
        self.logger.setLevel(logging.WARNING)
        self.logger.warning(log_this)

    def debug(self, log_this):
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug(log_this)

    def error(self, log_this):
        self.logger.setLevel(logging.ERROR)
        self.logger.error(log_this)

    def critical(self, log_this):
        self.logger.setLevel(logging.CRITICAL)
        self.logger.critical(log_this)


class ErrorMessage:
    """doc..."""

    def __init__(self, message_name, message_version_number, message_creation_timestamp, message_id, source_system,
                message_identity_number, target_system, system, host, resource, log_message, error_code, severity, time,
                business_flow_id):
        """Constructor"""
        self.message_name = message_name
        self.message_version_number = message_version_number
        self.message_creation_timestamp = message_creation_timestamp
        self.message_id = message_id
        self.source_system = source_system
        self.message_identity_number = message_identity_number
        self.business_keys = {"message_identity_Number": self.message_identity_number}
        self.target_system = target_system
        self.system = system
        self.host = host
        self.resource = resource
        self.log_message = log_message
        self.stack_trace = error_code
        self.severity = severity
        self.time = time
        self.business_flow_id = business_flow_id

    @staticmethod
    def create_message(self):
        message = {}
        metadata = {
                "message_name": self.message_name,
                "message_version_number": self.message_version_number,
                "message_creation_timestamp": self.message_creation_timestamp,
                "message_id": self.message_id,
                "source_system": self.source_system,
                "business_keys": {"message_identity_Number": self.message_identity_number}
                 }
        message_data = {
                "target_system": self.target_system,
                "system": self.system,
                "host": self.host,
                "resource": self.resource,
                "log_message": self.log_message,
                "error_code": self.stack_trace,
                "severity": self.severity,
                "time": self.time,
                "business_flow_id": self.business_flow_id
            }
        message.update(metadata)
        message.update(message_data)

        return message