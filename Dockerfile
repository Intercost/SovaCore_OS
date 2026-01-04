# Use a Python base image
FROM python:3.10-slim

# Install system dependencies (Git, Node.js, and GitHub CLI)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install gh -y

# Install Vercel and Railway CLIs globally
RUN npm install -g vercel railway

# Set working directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Set environment variables (Railway will override these from its dashboard)
ENV PROJECT_DESKTOP_PATH=/tmp/projects

# This Dockerfile is generic. 
# On Railway, you will create 4 separate services, 
# and for each, you will set the 'Start Command' to:
# python prime.py  (for the Prime service)
# python alpha.py  (for the Alpha service), etc.