# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install system packages, including the PostgreSQL client
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application files into the container
COPY . .

# Expose port 8000
EXPOSE 8000

# Define the command to run the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
