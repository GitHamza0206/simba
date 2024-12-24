
# MigiBot

A Role-Based Retrieval Augmented Generation (RAG) System for Enterprise Information Management

## Overview
MigiBot is a RAG system that retrieves information based on user roles and policies, ensuring secure and contextual access to enterprise knowledge.

## Project Structure

```
backend/
frontend/
docker-compose.yml
```

## Getting Started

first navigate to migibot directory
export your openai api key

```
export OPENAI_API_KEY=your_api_key
```

install docker and docker-compose (if not already installed) check documentation for installation instructions
then run the following command to start the application
```
docker-compose up --build 
```

navigate to http://localhost:5173 to access the frontend
