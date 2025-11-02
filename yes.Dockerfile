# Use an official Python runtime as parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements (if you have one) else copy just main.py and whatever modules
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# If your bot requires environment variables, declare them (example)
ENV DISCORD_TOKEN=""

# Run the bot
CMD ["python", "main.py"]