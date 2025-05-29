FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    gnupg \
    curl \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Run the app
CMD ["python", "app.py"]
