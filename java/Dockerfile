FROM maven:3.9-eclipse-temurin-25 AS builder

ARG MODULE=rest-api
WORKDIR /build

COPY contracts /build/contracts
COPY java /build/java

RUN mvn -f /build/java/pom.xml -pl ${MODULE} -am clean package -DskipTests

FROM eclipse-temurin:25-jre-alpine

ARG MODULE=rest-api
WORKDIR /app

COPY contracts /app/contracts
COPY --from=builder /build/java/${MODULE}/target/${MODULE}-1.0.0.jar /app/app.jar

ENV SEED_DATA_PATH=/app/contracts/seed/initial_data.json
ENV WSDL_PATH=/app/contracts/soap/streaming.wsdl

EXPOSE 8081 8082 8083 50052

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
