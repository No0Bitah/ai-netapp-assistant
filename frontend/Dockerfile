FROM node:20-alpine

WORKDIR /usr/src/app

# Copy package files
COPY package.json pnpm-lock.yaml* yarn.lock* package-lock.json* ./

# Install dependencies
RUN if [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i; \
    elif [ -f yarn.lock ]; then yarn; \
    else npm i; fi

# Add local node binaries to PATH
ENV PATH=/usr/src/app/node_modules/.bin:$PATH

# Copy source files (node_modules excluded via .dockerignore)
COPY . .

# Expose Vite port
EXPOSE 5173


# Start dev server
CMD ["npm", "run", "dev"]