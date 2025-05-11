FROM node:18-alpine

WORKDIR /app

# Install necessary build tools and dependencies
RUN apk add --no-cache python3 make g++ git

# Copy package files for better layer caching
COPY package*.json ./

# Install dependencies
RUN npm ci

# Add node_modules/.bin to PATH
ENV PATH="/app/node_modules/.bin:$PATH"

# Copy source code
COPY . .

# Ensure all required packages are installed
RUN npm install remark-math rehype-katex && \
    npm install @rollup/rollup-linux-x64-gnu && \
    npm install rehype-sanitize remark-gfm && \
    npm install date-fns --save

EXPOSE 5173

# Use Vite's development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]