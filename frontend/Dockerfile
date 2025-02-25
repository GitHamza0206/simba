FROM node:18-slim

WORKDIR /app

# Install necessary build tools
RUN apt-get update && \
    apt-get install -y python3 make g++ git && \
    rm -rf /var/lib/apt/lists/*

# Copy package files first for better caching
COPY package*.json ./


# Install dependencies and the Rollup binary
RUN npm ci && \
    npm install @rollup/rollup-linux-x64-gnu

# Add node_modules/.bin to PATH
ENV PATH="/app/node_modules/.bin:$PATH"

# Copy source code
COPY . .

EXPOSE 5173

# Use Vite's development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]