import datetime
import os

import functions_framework
from google.cloud import compute_v1
import logging
from flask import render_template


@functions_framework.http
def start_vm_web(request):
    """
    HTTP Cloud Function that checks the status of a specified Google Compute Engine VM instance. If the instance is not running, it starts the instance. The function returns an HTML page indicating the current status of the server and provides instructions for connecting to the Minecraft server if it is running.
    """
    try:
        logging_format = "[%(asctime)s] %(levelname)s: %(message)s"
        logging.basicConfig(level=logging.INFO, format=logging_format)
        logging.info(
            "Received request to check VM status and start if necessary.")
        # required for starting the instance and checking its status
        PROJECT_ID = os.environ.get("PROJECT_ID")
        ZONE = os.environ.get("ZONE")
        INSTANCE = os.environ.get("INSTANCE")
        # optional environment variable for Minecraft server port, default to 19132 if not set
        MC_SERVER_PORT = os.environ.get("MC_SERVER_PORT", "19132")

        operation_client = compute_v1.ZoneOperationsClient()
        # Check if all required environment variables are set
        if not all([PROJECT_ID, ZONE, INSTANCE]):
            logging.warning("Missing environment variables.")
            # return an error message in HTML format if any required environment variable is missing
            return render_template("index.html", status="error", message="❌ Missing environment variables.", error_message="Some environment variables are not set. Please check the server configuration."), 500

        logging.info(
            f"Checking status of instance '{INSTANCE}' in project '{PROJECT_ID}' and zone '{ZONE}'.")
        client = compute_v1.InstancesClient()
        instance_info = client.get(
            project=PROJECT_ID, zone=ZONE, instance=INSTANCE)
        status = instance_info.status

        if status == "TERMINATED":
            # instance is stopped, start it
            operation_request = compute_v1.ListZoneOperationsRequest(
                project=PROJECT_ID, zone=ZONE, filter=f"targetLink:instances/{INSTANCE}", max_results=3)
            operations = operation_client.list(
                operation_request)
            for operation in operations:
                operation_time = datetime.fromisoformat(
                    # Remove 'Z' and convert to datetime
                    operation.insert_time[:-1])
                if operation_time > datetime.now() - datetime.timedelta(minutes=5):
                    error = operation.error.errors[0] if operation.error and operation.error.errors else None
                    if error:
                        logging.error(
                            f"Recent operation error: {error.message}")
                        return render_template("index.html", status="error", message="❌ Error starting server.", error_message=f"An error occurred while starting the server: {error.message}"
                                               ), 500
            client.start(project=PROJECT_ID, zone=ZONE, instance=INSTANCE)
            logging.info(
                f"Sent start request for instance '{INSTANCE}' in project '{PROJECT_ID}' and zone '{ZONE}'.")
            return render_template("index.html", status="starting", message="⏳ Starting server...",
                                   ), 202

        elif status == "RUNNING":
            # instance is already running, return the IP address and port
            logging.info(f"Instance '{INSTANCE}' is running.")
            ip = instance_info.network_interfaces[0].access_configs[0].nat_i_p
            return render_template("index.html", status="running", message="✅ Server is running!", ip=ip, port=MC_SERVER_PORT)

        else:
            # instance is in some other state (e.g. PROVISIONING, STAGING), show the current status and a loading indicator
            logging.info(f"Instance '{INSTANCE}' is in status: {status}")
            return render_template("index.html", status="unknown", message=f"Current status: {status}")
    except Exception as e:
        # Log the error and return a generic error message in HTML format
        logging.error(f"Error occurred: {e}")
        return render_template("index.html", status="error", message="❌ An error occurred while checking the server status.", error_message="An error occurred. Please try again later."), 500
