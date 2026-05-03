FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY widget/ /usr/share/nginx/html/widget/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
