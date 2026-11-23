package br.unifor.distribuidos.graphql;

import br.unifor.distribuidos.common.service.StreamingService;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class GraphqlApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(GraphqlApiApplication.class, args);
    }

    @Bean
    public StreamingService streamingService() {
        return new StreamingService();
    }
}
