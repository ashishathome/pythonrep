import os
from google.cloud import logging_v2
from datetime import datetime

def __init__(self):
    '''
    Constructor
    '''
    
def create_message(project_id, function_name, function_region, business_flow_id, message_name, log_message, severity, alert_id, stack_trace, business_key, business_key_val):

    
    # Define a monitoring resource for this function
    # Monitored Resources: https://cloud.google.com/logging/docs/api/v2/resource-list#resource-indexes
    # Logging tutorial: https://googleapis.dev/python/logging/latest/usage.html
    # Logger Python API: https://googleapis.dev/python/logging/latest/logger.html

    monitoredResource = logging_v2.resource.Resource (
            type="cloud_function",
            labels={
                "project_id": project_id,
                "function_name": function_name,
                "region": function_region,
            },
        )

    logname = 'E2E_MONITORING_LOG'
    logger = logging_v2.Client().logger(logname)
    

    messageData = {
        "businessKeys" : {
            business_key: business_key_val
            },
            "message_name": message_name
    }

    message = {
    "flowId": business_flow_id,
    "logMessage": log_message,
    "messageData": messageData,
    "stack_trace": stack_trace,
    "alertId": alert_id
    }

    logger.log_struct(message, resource=monitoredResource, severity=severity, timestamp=datetime.now() )
            

