FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Start the application in dev mode
CMD ["pnpm", "run", "dev"]
