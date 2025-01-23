# Simba Backend

This documentation is for Simba headless KMS 

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Run the FastAPI server:
```bash
poetry run uvicorn main:app --reload
```

#TODO:
Add libheif to docker 


## API Endpoints

- 'GET /': Root endpoint, returns a hello world message
- 'GET /routes': Lists all available routes
- 'WS /ws/stream': WebSocket endpoint for real-time communication

## Development

This project uses Poetry for dependency management and requires Python >=3.11,< 3.13.

## Environment Variables

Create a '.env' file in the root directory with your configuration.

for unstructured , run the following command:

for windows install pyenv 
```bash
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```
the python version is located in the .python-version file

```bash
pyenv install 
```

**only for windows**
Install poetry
```bash
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

```

exectue poetry for the first time
```bash
poetry install
poetry shell
```



# Using local models

## ollama

first you need to pull the model using ollama

```bash
ollama run llama3.1:8b # or any other model     
```

then you need to update the config.yaml file with the model name

```yaml
llm:
  provider: "ollama"
  model_name: "llama3.1:8b"
```

## vllm

first you need to pull the model using vllm

```bash
vllm run meta-llama/Llama-3.1-8B-Instruct
```

then you need to update the config.yaml file with the model name

```yaml
llm:
  provider: "vllm"
  model_name: "meta-llama/Llama-3.1-8B-Instruct"
```