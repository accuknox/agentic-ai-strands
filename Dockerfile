# Use Ubuntu as the base image
FROM public.ecr.aws/docker/library/alpine:3.21.3
#FROM public.ecr.aws/ubuntu/ubuntu:22.04

# Set environment variables to avoid user interaction
#ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install basic packages
RUN apk update && apk add --no-cache --update python3 && ln -sf python3 /usr/bin/python

RUN python3 -m venv .venv && \
	. .venv/bin/activate && \
	python3 -m ensurepip && \
	pip3 install --no-cache --upgrade pip setuptools

RUN . .venv/bin/activate && \
	pip install --no-cache --upgrade strands-agents strands-agents-tools flask plotly pandas

# Set working directory
WORKDIR /app

# Copy local files into the container (if any)
COPY flask-app.py /app
COPY start-server.sh /app

# Default command
CMD [ "/app/start-server.sh" ]

