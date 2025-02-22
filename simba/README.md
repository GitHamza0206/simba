# Simba Backend

This documentation is for Simba portable KMS backend

## Setup

This step should be done in the root directory if not please refer to [README.md](/README.md) for more information


## Development

This project uses Poetry for dependency management and requires Python >=3.11,< 3.13.

## Known issues 

- [windows] UnstrucutredLoader may require tesseract installation




## Using local models

### ollama

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

coming soon... 

