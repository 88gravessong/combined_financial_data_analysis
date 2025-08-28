# Docker 部署指南

## 使用 docker-compose

```bash
docker-compose build
docker-compose up -d
```

访问: http://localhost:1001

停止服务:

```bash
docker-compose down
```

## 直接使用 Docker

```bash
docker build -t financial-analysis .
docker run -d -p 1001:8080 --name financial-app financial-analysis
```
