# MC server toggle script for Google Cloud Functions
This is a serverless function that starts a Minecraft server on demand. It uses Google Cloud Functions and Google Compute Engine to create and manage the Minecraft server instance.
## Environment Variables
- `PROJECT_ID`: The ID of your Google Cloud project.
- `ZONE`: The zone where your Minecraft server instance is located (e.g. `us-central1-a`).
- `INSTANCE`: The name of your Minecraft server instance.
- `MC_SERVER_PORT`: (Optional) The port number your Minecraft server is running on. Defaults to `19132` if not set.

You can use `.env-template` as a template for setting up your environment variables. Make sure to replace the placeholder values with your actual project ID, zone, instance name, and optionally the Minecraft server port.
## Usage
1. Deploy the function to Google Cloud Functions with the required environment variables.
2. When you access the function's URL, it will check the status of the Minecraft server instance:
   - If the instance is stopped, it will start the instance and show a loading indicator until it's running.
   - If the instance is already running, it will display the server's IP address and port number.
   - If any required environment variable is missing, it will show an error message.
3. Once the server is running, you can connect to it using the displayed IP address and port number in your Minecraft client.