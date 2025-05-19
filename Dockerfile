# Use Ubuntu as the base image
FROM public.ecr.aws/ubuntu/ubuntu:22.04

# Set environment variables to avoid user interaction
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install basic packages
RUN apt-get update && \
    apt-get install -y \
    curl \
    vim \
    python3 \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python -m venv .venv && \
	source .venv/bin/activate && \
	pip install strands-agents strands-agents-tools flask plotly kaleido pandas

# Set working directory
WORKDIR /app

# Copy local files into the container (if any)
COPY flask-app.py /app

# Default command
CMD [ "bash" ]

