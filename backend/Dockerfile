FROM eclipse-temurin:21-jre-alpine

RUN apk add --no-cache tini

WORKDIR /server

EXPOSE 25565

ENTRYPOINT ["tini", "--"]
CMD ["java", "-jar", "server.jar", "nogui"]
