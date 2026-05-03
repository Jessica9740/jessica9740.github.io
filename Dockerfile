FROM nginx:alpine
COPY output/ /usr/share/nginx/html/
EXPOSE 80
