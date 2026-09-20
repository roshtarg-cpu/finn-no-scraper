# Use official Apify Python base image with Python 3.11
FROM apify/actor-python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only for efficiency)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy source code
COPY . ./

# Run the actor
CMD ["python", "-m", "src.main"]
