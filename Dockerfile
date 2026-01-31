# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /code
WORKDIR /code

# Set permissions for local cache (useful for Hugging Face Spaces)
RUN mkdir -p /code/cache && chmod -R 777 /code/cache
ENV TRANSFORMERS_CACHE=/code/cache
ENV HF_HOME=/code/cache

# Copy the requirements file into the container
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the application code
COPY . /code

# Create necessary directories for the app
RUN mkdir -p /code/pdfs_demystify /code/video_consents
RUN chmod -R 777 /code/pdfs_demystify /code/video_consents

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
