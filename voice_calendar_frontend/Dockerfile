# 阶段 1：构建静态资源
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
# 使用淘宝 NPM 镜像加速 npm install
RUN npm config set registry https://registry.npmmirror.com
RUN npm install
COPY . .
RUN npm run build

# 阶段 2：服务静态文件 (使用 Nginx)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
