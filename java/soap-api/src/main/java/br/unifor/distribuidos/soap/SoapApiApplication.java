package br.unifor.distribuidos.soap;

import br.unifor.distribuidos.common.service.StreamingService;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class SoapApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(SoapApiApplication.class, args);
    }

    @Bean
    public StreamingService streamingService() {
        return new StreamingService();
    }
}
