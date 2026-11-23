package br.unifor.distribuidos.rest;

import br.unifor.distribuidos.common.service.StreamingService;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class RestApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(RestApiApplication.class, args);
    }

    @Bean
    public StreamingService streamingService() {
        return new StreamingService();
    }
}
