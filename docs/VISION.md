# Simba Vision Document

## The Vision

**Simba is the open-source customer service assistant that businesses can deploy in minutes, not months.**

We believe every company deserves world-class AI-powered customer support, regardless of their engineering resources. Simba makes this possible through a simple embed, backed by enterprise-grade intelligence.

---

## Mission Statement

> To democratize AI-powered customer service by providing an open-source, embeddable solution that answers questions **fast** and **accurately**.

---

## The Problem We Solve

### Current Reality
1. **Enterprise solutions are expensive** - $50K+ annual contracts
2. **DIY is complex** - Requires ML engineers, infrastructure, months of work
3. **Generic chatbots fail** - Low accuracy, frustrated customers, brand damage
4. **Data stays siloed** - Knowledge spread across docs, wikis, tickets

### Our Solution
- **Open source** - Free to use, modify, and self-host
- **One-line embed** - JavaScript snippet or React component
- **Knowledge-first** - Connect your docs, FAQs, and knowledge base
- **Accuracy-obsessed** - Strong evaluations ensure quality responses

---

## Target Users

### Primary: Developer-Led Companies
- Startups and scale-ups (10-500 employees)
- Developer-first tools and SaaS products
- Companies with existing documentation

### Secondary: Agencies & Consultants
- Building for multiple clients
- Need white-label solutions
- Value open-source flexibility

### Tertiary: Enterprises (Self-Hosted)
- Data sovereignty requirements
- Custom compliance needs
- Internal support use cases

---

## Core Principles

### 1. Speed is Everything
Customers expect instant answers. Our target:
- **< 2 seconds** for any response
- **Real-time** streaming responses
- **Instant** widget load

### 2. Accuracy is Non-Negotiable
Wrong answers are worse than no answers:
- **Mandatory evals** on every AI feature
- **Citation-backed** responses
- **Confidence scoring** to prevent hallucinations
- **Continuous improvement** via feedback loops

### 3. Developer Experience First
If developers don't love it, it won't get adopted:
- **< 5 minutes** to first working integration
- **Excellent documentation** with examples
- **TypeScript-first** with full type safety
- **Flexible APIs** for custom implementations

### 4. Open Source, Open Standards
We build in public:
- **MIT licensed** - use it anywhere
- **No vendor lock-in** - swap any component
- **Community-driven** - PRs welcome
- **Transparent roadmap** - built with users

---

## Product Components

### 1. Simba Widget (npm package)
The embeddable frontend that customers interact with.
```
@simba/widget
- Chat interface
- Search modal
- FAQ accordion
- Feedback collection
```

### 2. Simba Backend (FastAPI)
The intelligence layer that powers everything.
```
simba-core
- Document processing
- Vector search
- LLM orchestration
- Conversation management
```

### 3. Simba Dashboard
Admin interface for managing knowledge and monitoring.
```
- Document management
- Conversation analytics
- Eval metrics dashboard
- Configuration UI
```

### 4. Simba SDK (Python)
Programmatic access for advanced use cases.
```
simba-client
- Full API access
- Batch operations
- Custom integrations
```

---

## Key Differentiators

| Feature | Simba | Intercom | Zendesk | DIY |
|---------|-------|----------|---------|-----|
| Open Source | Yes | No | No | N/A |
| Self-Hostable | Yes | No | No | Yes |
| Time to Deploy | Minutes | Days | Weeks | Months |
| Built-in Evals | Yes | No | No | No |
| Knowledge-First | Yes | Partial | Partial | Varies |
| Cost | Free* | $$$$ | $$$$ | Engineering Time |

*Self-hosted. Managed cloud coming soon.

---

## Success Metrics

### Product Metrics
- **Time to First Value**: < 5 minutes from signup to working widget
- **Resolution Rate**: > 70% of queries answered without human
- **User Satisfaction**: > 4.5/5 average rating
- **Response Accuracy**: > 95% factually correct (per evals)

### Business Metrics
- **GitHub Stars**: Leading indicator of interest
- **npm Downloads**: Adoption measurement
- **Active Deployments**: Real usage tracking
- **Community Contributors**: Health of open source

---

## Roadmap Overview

### Phase 1: Foundation (Current)
- [ ] Core chat widget
- [ ] Document ingestion pipeline
- [ ] Basic retrieval and generation
- [ ] Evaluation framework
- [ ] npm package publishing

### Phase 2: Polish
- [ ] Advanced theming system
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Webhook integrations
- [ ] Rate limiting and quotas

### Phase 3: Scale
- [ ] Multi-tenant architecture
- [ ] Enterprise SSO
- [ ] Audit logging
- [ ] SLA guarantees
- [ ] Managed cloud option

### Phase 4: Intelligence
- [ ] Auto-learning from corrections
- [ ] Proactive suggestions
- [ ] Sentiment analysis
- [ ] Escalation workflows
- [ ] Agent handoff

---

## Technical Non-Negotiables

These are architectural decisions that should not be compromised:

1. **TypeScript everywhere** in frontend code
2. **Strong typing** in Python (Pydantic, type hints)
3. **Evaluations** for every AI feature
4. **PostgreSQL** as primary database
5. **Vector search** for retrieval (pgvector)
6. **Streaming responses** for chat
7. **< 50KB** widget bundle size
8. **API-first** design

---

## What We're NOT Building

Clarity on scope is as important as features:

- **Not a full helpdesk** - No ticketing system
- **Not a CRM** - No contact management
- **Not a live chat** - No human agent routing (initially)
- **Not an AI builder** - No custom agent creation
- **Not analytics-first** - Support is the core, not data

---

## The Team Promise

As builders of Simba, we commit to:

1. **Shipping fast** - Bias for action over perfection
2. **Staying focused** - Saying no to feature creep
3. **Being transparent** - Public roadmap, open development
4. **Listening deeply** - User feedback shapes priorities
5. **Quality always** - Never ship broken software

---

## Join Us

Simba is built by and for the community. Whether you're a developer, designer, or just passionate about better customer service - we'd love your help.

- **Star us on GitHub**: Show your support
- **Try the widget**: Embed it in your project
- **Contribute**: Code, docs, or ideas welcome
- **Spread the word**: Tell your network

---

*"The best customer service is no customer service - the product just works. The second best is Simba."*
