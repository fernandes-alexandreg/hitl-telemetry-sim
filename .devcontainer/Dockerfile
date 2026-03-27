FROM mcr.microsoft.com/devcontainers/python:3.11

WORKDIR /workspace

COPY .devcontainer/requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && python -m ipykernel install --sys-prefix --name python3 --display-name "Python 3"
