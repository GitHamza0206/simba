
# Simba - Bring Your Knowledge into Your AI 

<!-- <a href="https://ibb.co/RHkRGcs"><img src="https://i.ibb.co/ryRDKHz/logo.jpg" alt="logo" border="0"></a> -->
[![Twitter Follow](https://img.shields.io/twitter/follow/zeroualihamza?style=social)](https://x.com/zerou_hamza)


Simba is an open source, portable KMS (knowledge management system) designed to integrate seamlessly with any Retrieval-Augmented Generation (RAG) system. With a modern UI and modular architecture, Simba allows developers to focus on building advanced AI solutions without worrying about the complexities of knowledge management.

| Just build your RAG, we take care of the knowledge |
|:------------------------------------------------------------:|


# Table of Contents


- [Simba - Bring Your Knowledge into Your AI](#simba---bring-your-knowledge-into-your-ai)
- [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Demo](#demo)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Local Development](#local-development)
  - [Backend](#backend)
  - [Frontend](#frontend)
  - [Launch with docker (Recommended)](#launch-with-docker-recommended)
  - [📂 Project Structure](#-project-structure)
  - [⚙️ Configuration](#️-configuration)
  - [Roadmap](#roadmap)
  - [🤝 Contributing](#-contributing)
  - [💬  Support \& Contact](#--support--contact)
  

## Features

- **🧩 Modular Architecture:** Plug in various vector stores, embedding models, chunkers, and parsers.
- **🖥️ Modern UI:** Intuitive user interface to visualize and modify every document chunk.
- **� Seamless Integration:** Easily integrates with any RAG-based system.
- **👨‍💻 Developer Focus:** Simplifies knowledge management so you can concentrate on building core AI functionality.
- **📦 Open Source & Extensible:** Community-driven, with room for custom features and integrations.

## Demo 

[![Watch the demo](/assets/thumbnail.png)](/assets/demo.mp4)

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- [Python](https://www.python.org/) 3.11+ &  [poetry](https://python-poetry.org/) 
- [Redis](https://redis.io/) 7.0+
- [Node.js](https://nodejs.org/) 20+
- [Git](https://git-scm.com/) for version control.
- (Optional) Docker for containerized deployment.

### Installation
**note :** Simba uses celery for heavy tasks like parsing. These tasks may be launched with gpu. In order to avoid infrastructure problem related we recommend to launch the app using Docker 
### Local Development

```bash
git clone https://github.com/GitHamza0206/simba.git
cd simba
```
## Backend

```bash
cd backend
```

0. Redis installation 
   make sure to have redis installed in your OS 
   ```bash
   #init redis server
    redis-server
   ```

1.  setup env
   
```bash
cp .env.example .env
```
then edit the .env file with your own values
```ini

OPENAI_API_KEY="" 
LANGCHAIN_TRACING_V2= #(optional - for langsmith tracing) 
LANGCHAIN_API_KEY="" #(optional - for langsmith tracing) 
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

2. install dependencies
```bash
poetry install
poetry shell OR source .venv/bin/activate (MAC/LINUX) OR .venv\Scripts\activate (WINDOWS)
```

3. run backend
```bash
python main.py OR uvicorn main:app --reload #for auto reload 
```
then navigate to <a>http:0.0.0.0:8000/docs</a> to access swagger ui (Optional)

4. run the parser with celery worker
```bash
celery -A tasks.parsing_tasks worker --loglevel=info
```
5. modify the config.yaml file to your needs

```bash
# config.yaml

project:
  name: "Simba"
  version: "1.0.0"
  api_version: "/api/v1"

paths:
  base_dir: null  # Will be set programmatically
  markdown_dir: "markdown"
  faiss_index_dir: "vector_stores/faiss_index"
  vector_store_dir: "vector_stores"

llm:
  provider: "openai" #or ollama (vllm coming soon)
  model_name: "gpt-4o" #or ollama model name
  temperature: 0.0
  max_tokens: null
  streaming: true
  additional_params: {}

embedding:
  provider: "huggingface" #or openai
  model_name: "BAAI/bge-base-en-v1.5" #or any HF model name
  device: "cpu"  # mps,cuda,cpu
  additional_params: {}

vector_store:
  provider: "faiss" 
  collection_name: "migi_collection"
  additional_params: {}

chunking:
  chunk_size: 512
  chunk_overlap: 200

retrieval:
  k: 5 #number of chunks to retrieve 

features:
  enable_parsers: true  # Set to false to disable parsing

celery: 
  broker_url: ${CELERY_BROKER_URL:-redis://redis:6379/0}
  result_backend: ${CELERY_RESULT_BACKEND:-redis://redis:6379/1}
```

## Frontend

Make sure to be in the root simba directory

```bash
cd frontend
npm install
npm run dev 
```
then navigate to <a>http:localhost:5173</a> to access the frontend


## Launch with docker (Recommended)

navigate to root simba directory

```bash
export OPENAI_API_KEY="" #(optional) 
docker-compose up --build 
```

## 📂 Project Structure

```bash
simba/
├── backend/              # Core processing engine
│   ├── api/              # FastAPI endpoints
│   ├── services/         # Document processing logic
│   ├── tasks/            # Celery task definitions
│   └── models/          # Pydantic data models
├── frontend/             # React-based UI
│   ├── public/           # Static assets
│   └── src/              # React components
├── docker-compose.yml    # Development environment
└── docker-compose.prod.yml # Production setup
```

## ⚙️ Configuration
the [config.yaml](/backend/config.yaml) file is used to configure the backend application.
You can change : 
- embedding model
- vector store
- chunking
- retrieval
- features
- parsers 

navigate to [backend/README.md](/backend/README.md) for more information


## Roadmap

- [ ] Add more documentation 
- [ ] Make simba work with any RAG system as an importable python package
- [ ] Add CI/CD pipeline
- [ ] Add control over chunking parameters
- [ ] Add more parsers 
- [ ] Add more vector stores
- [ ] Add more embedding models
- [ ] Add more retrieval models
- [ ] Enable role access control
- [ ] 

## 🤝 Contributing
Contributions are welcome! If you'd like to contribute to Simba, please follow these steps:

- Fork the repository.
- Create a new branch for your feature or bug fix.
- Commit your changes with clear messages.
- Open a pull request describing your changes.

## 💬  Support & Contact
For support or inquiries, please open an issue 📌 on GitHub or contact repo owner at [Hamza Zerouali](mailto:zeroualihamza0206@gmail.com)

