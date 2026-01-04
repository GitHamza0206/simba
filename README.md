<p align="center">
<img src="/assets/simba-logo.png" alt="Simba Logo" width="400" height="400"/>
</p>

<p align="center">
<strong>High-Efficiency Customer Service Assistant</strong>
</p>

<p align="center">
<a href="https://github.com/GitHamza0206/simba/blob/main/LICENSE">
<img src="https://img.shields.io/github/license/GitHamza0206/simba" alt="License">
</a>
<a href="https://github.com/GitHamza0206/simba/stargazers">
<img src="https://img.shields.io/github/stars/GitHamza0206/simba" alt="Stars">
</a>
<a href="https://github.com/GitHamza0206/simba/issues">
<img src="https://img.shields.io/github/issues/GitHamza0206/simba" alt="Issues">
</a>
<a href="https://pepy.tech/projects/simba-core"><img src="https://static.pepy.tech/badge/simba-core" alt="PyPI Downloads"></a>
<a href="https://www.npmjs.com/package/simba-chat-widget"><img src="https://img.shields.io/npm/v/simba-chat-widget" alt="npm"></a>
</p>

<p align="center">
<a href="https://www.producthunt.com/posts/simba-2?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-simba&#0045;2" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=863851&theme=light&t=1739449352356" alt="Simba - Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>
</p>

[![Twitter Follow](https://img.shields.io/twitter/follow/zeroualihamza?style=social)](https://x.com/zerou_hamza)

## What is Simba?

Simba is an open-source customer service assistant built for teams who need **full control** over their AI. Unlike black-box solutions, Simba is designed from the ground up around **evaluation** and **customization**, so you can measure performance, iterate fast, and tailor the assistant to your exact needs.

## Why Simba?

| Problem | Simba's Solution |
|---------|------------------|
| Can't measure AI quality | Built-in evaluation framework with retrieval and generation metrics |
| Generic responses | Fully customizable RAG pipeline with your own data |
| Hard to integrate | Drop-in npm package for instant website integration |
| Vendor lock-in | Open-source, self-hosted, swap any component |

## Key Features

- **Evaluation-First Design** - Track retrieval accuracy, generation quality, and latency out of the box. Know exactly how your assistant performs.
- **Fully Customizable** - Swap embedding models, LLMs, vector stores, chunking strategies, and rerankers. Your pipeline, your rules.
- **npm Package for Easy Integration** - Add a customer service chat widget to your website with a single npm install.
- **Modern Dashboard** - Manage documents, monitor conversations, and analyze performance from a clean UI.
- **Production-Ready** - Streaming responses, async processing, and scalable architecture.

## Quick Start

### Docker (Recommended)

The fastest way to get Simba running:

```bash
git clone https://github.com/GitHamza0206/simba.git
cd simba
```

Create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
```

Run with Docker:

```bash
# CPU
DEVICE=cpu make build && make up

# NVIDIA GPU
DEVICE=cuda make build && make up
```

Visit `http://localhost:3000` to access the dashboard.

### Manual Installation

If you prefer installing without Docker:

```bash
pip install simba-core
```

```bash
simba server
simba front
```

### Development Setup with Claude Code

If you're using [Claude Code](https://claude.ai/code), you can set up the project with a single command:

```bash
/setup --all
```

This will automatically install all dependencies (Python, frontend, npm package) and start the infrastructure services. Other options:

```bash
/setup --backend    # Python dependencies only
/setup --frontend   # Next.js + simba-chat only
/setup --services   # Start Docker infrastructure only
```

## Website Integration

Add Simba to your website with the npm package:

```bash
npm install simba-chat-widget
```

```jsx
import { SimbaChat } from 'simba-chat-widget';

function App() {
  return (
    <SimbaChat
      apiUrl="https://your-simba-instance.com"
      theme="light"
    />
  );
}
```

That's it. Your customers now have an AI assistant powered by your knowledge base.

## Evaluation & Metrics

Simba tracks what matters:

- **Retrieval Metrics** - Precision, recall, relevance scores
- **Generation Metrics** - Faithfulness, answer relevancy, latency
- **Conversation Analytics** - User satisfaction, resolution rates

Use these metrics to continuously improve your assistant's performance.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Your Website  │────▶│   Simba API     │────▶│  Vector Store   │
│  (npm package)  │     │   (FastAPI)     │     │  (Qdrant/FAISS) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        ▲
                               │                        │
                               ▼                        │
                        ┌─────────────────┐     ┌───────┴─────────┐
                        │      LLM        │     │     Celery      │
                        │ (OpenAI/Local)  │     │   (Ingestion)   │
                        └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │      Redis      │
                                                │  (Task Queue)   │
                                                └─────────────────┘
```

## Docker Deployment

```bash
# CPU
DEVICE=cpu make build && make up

# NVIDIA GPU
DEVICE=cuda make build && make up
```

## Customization Options

| Component | Options |
|-----------|---------|
| Vector Store | Qdrant, FAISS, Chroma |
| Embeddings | OpenAI, HuggingFace, Cohere |
| LLM | OpenAI, Anthropic, Local models |
| Reranker | Cohere, ColBERT, Cross-encoder |
| Parser | Docling, Unstructured, PyMuPDF |

## Roadmap

- [x] Core evaluation framework
- [x] npm chat widget
- [x] Streaming responses
- [ ] Multi-tenant support
- [ ] Advanced analytics dashboard
- [ ] Webhook integrations
- [ ] Fine-tuning pipeline

## Contributing

We welcome contributions! Fork the repo, create a branch, and submit a PR.

## Support

- Open an issue on [GitHub](https://github.com/GitHamza0206/simba/issues)
- Contact: [zeroualihamza0206@gmail.com](mailto:zeroualihamza0206@gmail.com)

## License

MIT License - use it however you want.
