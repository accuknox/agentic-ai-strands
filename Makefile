.PHONY: all build push

build:
	docker buildx build -t nyrahul/agentic-ai-strands .

push:
	docker push nyrahul/agentic-ai-strands
