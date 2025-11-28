# Use official Playwright image with Python + Browsers
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Copy entire project
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render automatically uses PORT env, but ok)
EXPOSE 5000

# Start API with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers", "1"]
