
# Simba

<!-- <a href="https://ibb.co/RHkRGcs"><img src="https://i.ibb.co/ryRDKHz/logo.jpg" alt="logo" border="0"></a> -->


A Headless KMS (Knowledge management system) integrable with any RAG based system (GraphRAG, Agentic RAG, Adaptive RAG...)

## Overview
It operates as a full stack app with backend made with python FastAPI and frontend made with Typescript React vite

## Quick start 
```
pip install simba 
simba run 
```

then navigate to <a>http:localhost:xxxx</a> to add knowledge base to simba 

## Project Structure

```
backend/
frontend/
docker-compose.yml
```

## Getting Started 

first navigate to simba directory
export your openai api key

```
export OPENAI_API_KEY=your_api_key
```

install docker and docker-compose (if not already installed) check documentation for installation instructions
then run the following command to start the application
```
docker-compose up --build 
```

**important note:** make sure that the VITE_API_URL is set to the server's ip address

## How to clean restart 
```
docker-compose down --volumes
docker system prune -a --volumes
docker-compose build --no-cache
docker-compose up
```

## How to run in production
```
docker-compose -f docker-compose.prod.yml up --build
```

navigate to http://localhost:5173 to access the frontend
