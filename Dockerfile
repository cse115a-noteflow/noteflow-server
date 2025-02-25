# Use the official Python image as the base image
FROM python:3.9

# Install Flask and Gunicorn
RUN pip install Flask flask_cors firebase_admin gunicorn

# Set the working directory in the container
WORKDIR /main

# Copy all files to the container
COPY . .

# Set environment variables
ENV PORT 8080

# Start Gunicorn with the correct entry point
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

