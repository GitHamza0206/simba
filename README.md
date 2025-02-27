<h1 align="center">Simba - Your Knowledge Management System</h1>

<p align="center">
<img src="/assets/logo.png" alt="Simba Logo" width="400", height="400"/>
</p>

<p align="center">
<strong>Connect your knowledge to any RAG system</strong>
</p>

<p align="center">
<a href="https://www.producthunt.com/posts/simba-2?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-simba&#0045;2" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=863851&theme=light&t=1739449352356" alt="Simba&#0032; - Connect&#0032;your&#0032;Knowledge&#0032;into&#0032;any&#0032;RAG&#0032;based&#0032;system | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>
</p>

<p align="center">


<a href="https://github.com/GitHamza0206/simba/blob/main/LICENSE">
<img src="https://img.shields.io/github/license/GitHamza0206/simba" alt="License">
</a>
<a href="https://github.com/GitHamza0206/simba/stargazers">
<img src="https://img.shields.io/github/stars/GitHamza0206/simba" alt="Stars">
</a>
<a href="https://github.com/GitHamza0206/simba/network/members">
<img src="https://img.shields.io/github/forks/GitHamza0206/simba" alt="Forks">
</a>
<a href="https://github.com/GitHamza0206/simba/issues">
<img src="https://img.shields.io/github/issues/GitHamza0206/simba" alt="Issues">
</a>
<a href="https://github.com/GitHamza0206/simba/pulls">
<img src="https://img.shields.io/github/issues-pr/GitHamza0206/simba" alt="Pull Requests">
</a>
<a href="https://pepy.tech/projects/simba-core"><img src="https://static.pepy.tech/badge/simba-core" alt="PyPI Downloads"></a>
</p>

<!-- <a href="https://ibb.co/RHkRGcs"><img src="https://i.ibb.co/ryRDKHz/logo.jpg" alt="logo" border="0"></a> -->
[![Twitter Follow](https://img.shields.io/twitter/follow/zeroualihamza?style=social)](https://x.com/zerou_hamza)

Simba is an open source, portable KMS (knowledge management system) designed to integrate seamlessly with any Retrieval-Augmented Generation (RAG) system. With a modern UI and modular architecture, Simba allows developers to focus on building advanced AI solutions without worrying about the complexities of knowledge management.

# Table of Contents

- [Table of Contents](#table-of-contents)
  - [🚀 Features](#-features)
  - [🎥 Demo](#-demo)
  - [🛠️ Getting Started](#️-getting-started)
    - [📋 Prerequisites](#-prerequisites)
    - [📦 Installation](#-installation)
    - [🔑 Configuration](#-configuration)
    - [🚀 Run Simba](#-run-simba)
    - [🐳 Docker Deployment](#-docker-deployment)
      - [Run on Specific Hardware](#run-on-specific-hardware)
  - [🏁 Roadmap](#-roadmap)
  - [🤝 Contributing](#-contributing)
  - [💬 Support \& Contact](#-support--contact)

## 🚀 Features

- **🧩 Modular Architecture:** Plug in various vector stores, embedding models, chunkers, and parsers.
- **🖥️ Modern UI:** Intuitive user interface to visualize and modify every document chunk.
- **🔗 Seamless Integration:** Easily integrates with any RAG-based system.
- **👨‍💻 Developer Focus:** Simplifies knowledge management so you can concentrate on building core AI functionality.
- **📦 Open Source & Extensible:** Community-driven, with room for custom features and integrations.

## 🎥 Demo

![Watch the demo](/assets/demo.gif)

## 🛠️ Getting Started

### 📋 Prerequisites

Before you begin, ensure you have met the following requirements:

- [Python](https://www.python.org/) 3.11+ & [poetry](https://python-poetry.org/)
- [Redis](https://redis.io/) 7.0+
- [Node.js](https://nodejs.org/) 20+
- [Git](https://git-scm.com/) for version control.
- (Optional) Docker for containerized deployment.

### 📦 Installation

install simba-core:

```bash
pip install simba-core

```

Clone the repository and install dependencies:

```bash
git clone https://github.com/GitHamza0206/simba.git
cd simba
poetry config virtualenvs.in-project true
poetry install
source .venv/bin/activate 
```

### 🔑 Configuration

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key
REDIS_HOST=localhost
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

```

create or update config.yaml file in the root directory:

```yaml
# config.yaml

project:
  name: "Simba"
  version: "1.0.0"
  api_version: "/api/v1"

paths:
  base_dir: null  # Will be set programmatically
  faiss_index_dir: "vector_stores/faiss_index"
  vector_store_dir: "vector_stores"

llm:
  provider: "openai"
  model_name: "gpt-4o-mini"
  temperature: 0.0
  max_tokens: null
  streaming: true
  additional_params: {}

embedding:
  provider: "huggingface"
  model_name: "BAAI/bge-base-en-v1.5"
  device: "mps"  # Changed from mps to cpu for container compatibility
  additional_params: {}

vector_store:
  provider: "faiss"
  collection_name: "simba_collection"

  additional_params: {}

chunking:
  chunk_size: 512
  chunk_overlap: 200

retrieval:
  k: 5

celery: 
  broker_url: ${CELERY_BROKER_URL:-redis://redis:6379/0}
  result_backend: ${CELERY_RESULT_BACKEND:-redis://redis:6379/1}


```

### 🚀 Run Simba

Run the server:
```bash
simba server
```

Run the frontend:
```bash
simba front 
```

Run the parsers:
```bash
simba parsers
```
### 🐳 Docker Deployment


#### Run on Specific Hardware

**For CPU:**
```bash
DEVICE=cpu make build
DEVICE=cpu make up
```

**For NVIDIA GPU with Ollama:**
```bash
DEVICE=cuda make build
DEVICE=cuda make up
```

**For Apple Silicon:**
```bash
# Note: MPS (Metal Performance Shaders) is NOT supported in Docker containers
# For Docker, always use CPU mode even on Apple Silicon:
DEVICE=cpu make build
DEVICE=cpu make up

```

**Run with Ollama service (for CPU):**
```bash
DEVICE=cpu ENABLE_OLLAMA=true make up
```

**Run in background mode:**
```bash
# All commands run in detached mode by default
```


For detailed Docker instructions, see the [Docker deployment guide](docker/README).



## 🏁 Roadmap
 
- [ ] 💻 pip install simba-core
- [ ] 🔧 pip install simba-sdk
- [ ] 🌐 www.simba-docs.com 
- [ ] 🔒 Adding Auth & access management
- [ ] 🕸️ Adding web scraping
- [ ] ☁️ Pulling data from Azure / AWS / GCP
- [ ] 📚 More parsers and chunkers available
- [ ] 🎨 Better UX/UI

  

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to Simba, please follow these steps:

  

- Fork the repository.

- Create a new branch for your feature or bug fix.

- Commit your changes with clear messages.

- Open a pull request describing your changes.

  

## 💬 Support & Contact

For support or inquiries, please open an issue 📌 on GitHub or contact repo owner at [Hamza Zerouali](mailto:zeroualihamza0206@gmail.com)