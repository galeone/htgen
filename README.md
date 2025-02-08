# Hashtag Generator - AI-Powered PWA

A Progressive Web Application (PWA) that uses Google Cloud's Vertex AI with Gemini Flash to analyze images and generate relevant hashtags. The application combines multimodal AI capabilities to understand image content and generate appropriate hashtags, making it easier to tag and categorize images for social media.

## Features

- Image analysis using Vertex AI's Gemini Flash
- Progressive Web App (PWA) for native-like experience
- Google Cloud Storage integration for image storage
- AI-Generated UI/UX design
- Support for multiple image formats (PNG, JPG, JPEG, GIF, WEBP)

## Local Development

To run the application locally, follow these steps:

1. Create the virtual environment and install the dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create the `.env.dev` file with the following environment variables:
   ```bash
   GOOGLE_CLOUD_PROJECT="your-project-id"
   BUCKET_NAME="your-bucket-name"
   ```
   Of course, replace `your-project-id` and `your-bucket-name` with your actual Google Cloud project ID and bucket name.
3. Run it using the following command:
   ```bash
   python app.py
   ```

If you use vscode the `launch.json` file is already configured to run the application.

## Running with Docker - Production Mode

There are two ways to run the application in production mode using Docker:

### Option 1: Using Docker Compose (Recommended)

1. Ensure you have your Google Cloud credentials JSON file ready.
2. Set the `GOOGLE_CREDENTIALS_PATH` environment variable to point to your credentials file:
   ```bash
   export GOOGLE_CREDENTIALS_PATH=/path/to/your/credentials.json
   ```
3. Start the application:
   ```bash
   docker compose up --no-recreate
   ```

### Option 2: Using Docker CLI

1. First, ensure you have your Google Cloud credentials JSON file ready.
2. Export the following environment variables:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export BUCKET_NAME="your-bucket-name"
   ```
3. Build the Docker image with the following command:
   ```bash
   docker build -t htgen .
   ```
4. Run the Docker container with the following command:
   ```bash
   docker run -p 8000:8000 \
     -e GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT \
     -e BUCKET_NAME=$BUCKET_NAME \
     -e GOOGLE_APPLICATION_CREDENTIALS="/app/credentials.json" \
     -v /path/to/your/credentials.json:/app/credentials.json \
     htgen
   ```
    Replace `/path/to/your/credentials.json` with the path to your Google Cloud credentials JSON file.

### Environment Variables

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `BUCKET_NAME`: The Google Cloud Storage bucket name for storing images
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the credentials file inside the container (should be inside /app, so "/app/credentials.json" is the default value)
- `GOOGLE_CREDENTIALS_PATH`: (Docker Compose only) Path to your local credentials file

### Volume Mount

The service account credentials file needs to be mounted into the container. Both Docker Compose and the Docker CLI command map your local credentials file into the container at `/app/credentials.json`.

## Running as a Systemd Service

You can run the application as a systemd service to ensure it starts automatically on boot and is managed by the system.

1. Copy the service file to systemd directory:
   ```bash
   sudo cp htgen@.service /etc/systemd/system/
   ```

2. Edit the service file to set your paths and user:
   ```bash
   sudo nano /etc/systemd/system/htgen@.service
   ```
   Update the following:
   - Replace `WorkingDirectory=/home/plox/htgen/` with your project directory path
   - Update the `GOOGLE_CREDENTIALS_PATH` in ExecStart to point to your credentials file

3. Reload systemd to recognize the new service:
   ```bash
   sudo systemctl daemon-reload
   ```

4. Enable and start the service (replace `yourusername` with your system username):
   ```bash
   sudo systemctl enable htgen@yourusername
   sudo systemctl start htgen@yourusername
   ```

## PWA = Runs Everywhere

Note: https://chromeos.dev/en/publish/pwa-in-play followed for publishing on the Google Play Store.

- `keytool -list -v -keystore keystores/android.pwa -alias android -keypass $PDW1 -storepass $PWD2 | grep SHA256`
- `bubblewrap fingerprint add <fingerprint>`
- `cp assetlinks.json htgen/static/.well-known/assetlinks.json`

## Credits

Google Cloud credits are provided for this project. #VertexAISprint
