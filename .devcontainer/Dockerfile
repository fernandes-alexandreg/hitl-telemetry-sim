FROM mcr.microsoft.com/devcontainers/python:3.11

WORKDIR /workspace

COPY .devcontainer/requirements.txt .
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e . \
    && python -m ipykernel install --sys-prefix --name python3 --display-name "Python 3"
