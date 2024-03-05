# Use Python base image
FROM python:3.8

# Set environment variable for MongoDB URI


# Set up working directory
WORKDIR /app

# Copy Python application code
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose port for Python application
EXPOSE 8080

# Start Python application
CMD ["python", "server.py"]
