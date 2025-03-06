# Dockerfile for devcontainer
FROM mcr.microsoft.com/devcontainers/python:3

USER vscode

# For some reason defaults to root user
COPY --chown=vscode:vscode . /workspace
