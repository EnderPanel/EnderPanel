FROM eclipse-temurin:21-jre-jammy

RUN apt-get update -qq && apt-get install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*

WORKDIR /server

EXPOSE 25565

ENTRYPOINT ["tini", "--"]
CMD ["java", "-jar", "server.jar", "nogui"]
