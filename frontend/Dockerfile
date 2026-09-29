# Dev / demo container — production desktop builds use Tauri (see BUILD.md).
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ENV NEXT_PUBLIC_API_URL=http://host.docker.internal:8000/api/v1
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]
