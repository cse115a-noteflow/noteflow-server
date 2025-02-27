# Use the official Python image as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /

# Install Flask and Gunicorn
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy all files to the container
COPY . .

# Set environment variables
ENV PORT 8080

# Start Gunicorn with the correct entry point
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 api:create_app()
