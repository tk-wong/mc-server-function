import os

import functions_framework
from google.cloud import compute_v1
import logging


@functions_framework.http
def start_vm_web(request):
    logging.basicConfig(level=logging.INFO)
    logging.info("Received request to check VM status and start if necessary.")
    PROJECT_ID = os.environ.get("PROJECT_ID")
    ZONE = os.environ.get("ZONE")
    INSTANCE = os.environ.get("INSTANCE")
    MC_SERVER_PORT = os.environ.get("MC_SERVER_PORT", "19132")  # default to 19132 if not set
    # --------------------
    html_template = """
    <html>
        <head>
            <meta charset="utf-8">
            <title>Minecraft Server Status</title>
            {refresh_tag}
            <style>
                body {{ font-family: sans-serif; text-align: center; padding-top: 50px; background: #2c3e50; color: white; }}
                .status {{ font-size: 24px; font-weight: bold; padding: 20px; }}
                .ip {{ color: #2ecc71; font-size: 32px; border: 2px solid #2ecc71; display: inline-block; padding: 10px 20px; margin-top: 20px; }}
                .loader {{ border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 20px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <h1>Minecraft Server Status</h1>
            <div class="status">{message}</div>
            {content}
        </body>
    </html>
    """
    if not all([PROJECT_ID, ZONE, INSTANCE]):
        logging.warning("Missing environment variables.")
        return html_template.format(
            refresh_tag='',
            message="❌ Missing environment variables.",
            content='<p>Please check the server configuration.</p>'
        ) , 500
    try:
        logging.info(
            f"Checking status of instance '{INSTANCE}' in project '{PROJECT_ID}' and zone '{ZONE}'.")
        client = compute_v1.InstancesClient()
        instance_info = client.get(
            project=PROJECT_ID, zone=ZONE, instance=INSTANCE)
        status = instance_info.status


        if status == "TERMINATED":
            # 如果是關機狀態，發送啟動請求
            client.start(project=PROJECT_ID, zone=ZONE, instance=INSTANCE)
            logging.info(
                f"Sent start request for instance '{INSTANCE}' in project '{PROJECT_ID}' and zone '{ZONE}'.")
            return html_template.format(
                # 每 5 秒刷新一次
                refresh_tag='<script>setTimeout(() => { location.reload(); }, 5000);</script>',
                message="starting server...",
                content='<div class="loader"></div><p>server is starting. The page will refresh every 5 seconds until the server is ready...</p>'
            )

        elif status == "RUNNING":
            logging.info(f"Instance '{INSTANCE}' is running.")
            ip = instance_info.network_interfaces[0].access_configs[0].nat_i_p
            return html_template.format(
                refresh_tag='',
                message="✅ Server is running!",
                content=f'<div class="ip">ip: {ip}<br>Port: {MC_SERVER_PORT}</div><p>You can start Minecraft Bedrock and connect to the server using the IP address above. Please note that it may take a few minutes for the server to be fully ready.</p>'
            )

        else:
            # 處理其他過渡狀態（如 PROVISIONING, STAGING）
            logging.info(f"Instance '{INSTANCE}' is in status: {status}")
            return html_template.format(
                # 每 5 秒刷新一次
                refresh_tag='<script>setTimeout(() => { location.reload(); }, 5000);</script>',
                message=f"Current status: {status}",
                content='<div class="loader"></div><p>Processing...Please wait.</p>'
            )
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return html_template.format(
            refresh_tag='',
            message="❌ An error occurred while checking the server status.",
            content=f'<p>An error occurred. Please try again later.</p>'
        ) , 500
