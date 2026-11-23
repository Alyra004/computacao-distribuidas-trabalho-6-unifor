package br.unifor.distribuidos.grpc;

import br.unifor.distribuidos.common.service.StreamingService;
import io.grpc.Server;
import io.grpc.ServerBuilder;

import java.io.IOException;

/**
 * Entrega Java 4: Servidor gRPC standalone usando Netty e o núcleo StreamingService.
 */
public class GrpcApiApplication {

    public static void main(String[] args) throws IOException, InterruptedException {
        int port = Integer.parseInt(System.getenv().getOrDefault("GRPC_PORT", "50052"));
        StreamingService coreService = new StreamingService();

        Server server = ServerBuilder.forPort(port)
                .addService(new StreamingGrpcServiceImpl(coreService))
                .build()
                .start();

        System.out.println("Java gRPC StreamingService ativo na porta " + port);

        Runtime.getRuntime().addShutdownHook(new Thread(server::shutdown));
        server.awaitTermination();
    }
}
