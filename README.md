
# Simba

[![Build Status](https://img.shields.io/github/actions/workflow/status/yourorg/simba/ci.yml?branch=main)](https://github.com/yourorg/simba/actions)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen)](https://docs.simba-kms.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT)


<!-- <a href="https://ibb.co/RHkRGcs"><img src="https://i.ibb.co/ryRDKHz/logo.jpg" alt="logo" border="0"></a> -->


Simba is an open source, portable KMS (knowledge management system) designed to integrate seamlessly with any Retrieval-Augmented Generation (RAG) system. With a modern UI and modular architecture, Simba allows developers to focus on building advanced AI solutions without worrying about the complexities of knowledge management.
 
# Demo 

Demo here: 

## Table of Contents

- [Simba](#simba)
- [Demo](#demo)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [🚀 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Local Development](#local-development)
        - [Backend](#backend)
        - [Frontend](#frontend)
      - [Launch with docker](#launch-with-docker)
- [Configuration](#configuration)
  - [🧩 Project Structure](#-project-structure)

## Features

- **Modular Architecture:** Plug in various vector stores, embedding models, chunkers, and parsers.
- **Modern UI:** Intuitive user interface to visualize and modify every document chunk.
- **Seamless Integration:** Easily integrates with any RAG-based system.
- **Developer Focus:** Simplifies knowledge management so you can concentrate on building core AI functionality.
- **Open Source & Extensible:** Community-driven, with room for custom features and integrations.

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- [Python](https://www.python.org/) 3.11+ &  [poetry](https://python-poetry.org/) 
- [Redis](https://redis.io/) 7.0+
- [Node.js](https://nodejs.org/) 20+
- [Git](https://git-scm.com/) for version control.
- (Optional) Docker for containerized deployment.

### Installation
**note**: Simba uses celery for heavy tasks like parsing. These tasks may be launched with gpu. In order to avoid infrastructure problem related we recommend to launch the app using Docker 
### Local Development

```bash
git clone https://github.com/GitHamza0206/simba.git
cd simba
```
##### Backend

0. Redis installation 
   **note** : make sure to have redis installed in your OS 
   </br>

1.  setup env
   
```bash
cp .env.example .env
```
then edit the .env file with your own values
```ini

OPENAI_API_KEY="" 
LANGCHAIN_TRACING_V2= #(optional - for langsmith tracing) 
LANGCHAIN_API_KEY="" #(optiona l- for langsmith tracing) 
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

2. install dependencies
```bash
cd backend
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
celery -A backend.tasks.parsing_tasks worker --loglevel=info
```


##### Frontend

```bash
cd frontend
npm install
npm run dev 
```
then navigate to <a>http:localhost:5173</a> to access the frontend


####  Launch with docker

navigate to root simba directory

```bash
export OPENAI_API_KEY="" #(optional) 
docker-compose up --build 
```

# Configuration
the [config.yaml](/backend/config.yaml) file is used to configure the backend application.
You can change : 
- embedding model
- vector store
- chunking
- retrieval
- features
- parsers 

navigate to [backend/README.md](/backend/README.md) for more information

## 🧩 Project Structure

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


