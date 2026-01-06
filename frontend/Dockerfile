FROM node:20-alpine AS base

RUN corepack enable && corepack prepare pnpm@9 --activate

FROM base AS deps
WORKDIR /app

# Copy workspace config and lockfile
COPY pnpm-workspace.yaml pnpm-lock.yaml ./

# Copy all package.json files for workspace resolution
COPY frontend/package.json ./frontend/
COPY packages/simba-chat/package.json ./packages/simba-chat/

# Install all dependencies
RUN pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app

# Copy all node_modules from deps (including root and workspace packages)
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/frontend/node_modules ./frontend/node_modules
COPY --from=deps /app/packages/simba-chat/node_modules ./packages/simba-chat/node_modules

# Copy source files
COPY packages/simba-chat ./packages/simba-chat
COPY frontend ./frontend

WORKDIR /app/frontend

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN pnpm build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/frontend/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
