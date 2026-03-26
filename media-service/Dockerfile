FROM node:20-alpine

# Install system dependencies for media processing (ffmpeg)
# Build essentials for sharp (if needed depending on arch)
RUN apk add --no-cache ffmpeg

WORKDIR /app

# Install dependencies first (caching)
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build TypeScript code
RUN npm run build

EXPOSE 8000

# Start production server
CMD ["node", "dist/index.js"]
