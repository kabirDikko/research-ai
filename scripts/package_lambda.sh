#!/bin/bash
set -e

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy the Lambda function code
cp -r lambda_functions/ingest_function/* $TEMP_DIR/

# Install dependencies in the temporary directory
cd $TEMP_DIR
pip install -r requirements.txt -t .

# Remove PIL if it was installed as a dependency
echo "Removing PIL from the package..."
rm -rf PIL
rm -rf Pillow*
rm -rf pillow*

# Create the deployment package
echo "Creating deployment package..."
zip -r ../ingest_function.zip .

# Move the deployment package to the expected location
cd ..
mkdir -p dist
mv ingest_function.zip dist/

echo "Deployment package created at dist/ingest_function.zip"

# Clean up
rm -rf $TEMP_DIR
echo "Cleaned up temporary directory" 