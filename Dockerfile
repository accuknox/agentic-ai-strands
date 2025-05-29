# Use Ubuntu as the base image
FROM public.ecr.aws/docker/library/alpine:3.21.3

# Update the package list and install basic packages
RUN apk update && apk add --no-cache --update python3 && ln -sf python3 /usr/bin/python && mkdir ~/.aws

RUN python3 -m venv .venv && \
	. .venv/bin/activate && \
	python3 -m ensurepip && \
	pip3 install --no-cache --upgrade setuptools strands-agents strands-agents-tools flask

RUN cp /usr/bin/python3.12 /usr/bin/sandbox_python3.12

RUN sandbox_python3.12 -m venv sandbox && \
	. sandbox/bin/activate && \
	sandbox_python3.12 -m ensurepip && \
	pip3 install --no-cache --upgrade setuptools plotly pandas

# Set working directory
WORKDIR /app

# Copy local files into the container (if any)
COPY src/flask-app.py /app
COPY start-server.sh /app

# Default command
CMD [ "/app/start-server.sh" ]

