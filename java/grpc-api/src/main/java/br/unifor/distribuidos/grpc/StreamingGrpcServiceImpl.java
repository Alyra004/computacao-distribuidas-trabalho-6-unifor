package br.unifor.distribuidos.grpc;

import br.unifor.distribuidos.common.exception.ResourceNotFoundException;
import br.unifor.distribuidos.common.exception.ValidationException;
import br.unifor.distribuidos.common.service.StreamingService;
import br.unifor.distribuidos.grpc.proto.*;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;

import java.util.Map;
import java.util.function.Supplier;

/**
 * Implementação gRPC delegando todas as chamadas para br.unifor.distribuidos.common.service.StreamingService.
 */
public class StreamingGrpcServiceImpl extends StreamingServiceGrpc.StreamingServiceImplBase {
    private final StreamingService service;

    public StreamingGrpcServiceImpl(StreamingService service) {
        this.service = service;
    }

    private <T> void respond(StreamObserver<T> observer, Supplier<T> action) {
        try {
            observer.onNext(action.get());
            observer.onCompleted();
        } catch (ResourceNotFoundException ex) {
            observer.onError(Status.NOT_FOUND.withDescription(ex.getMessage()).asRuntimeException());
        } catch (ValidationException ex) {
            observer.onError(Status.INVALID_ARGUMENT.withDescription(ex.getMessage()).asRuntimeException());
        } catch (Exception ex) {
            observer.onError(Status.INTERNAL.withDescription(ex.getMessage()).asRuntimeException());
        }
    }

    private static Usuario toProto(br.unifor.distribuidos.common.model.Usuario u) {
        return Usuario.newBuilder()
                .setId(u.getId())
                .setNome(u.getNome())
                .setIdade(u.getIdade())
                .build();
    }

    private static Musica toProto(br.unifor.distribuidos.common.model.Musica m) {
        return Musica.newBuilder()
                .setId(m.getId())
                .setNome(m.getNome())
                .setArtista(m.getArtista())
                .build();
    }

    private static Playlist toProto(br.unifor.distribuidos.common.model.Playlist p) {
        return Playlist.newBuilder()
                .setId(p.getId())
                .setNome(p.getNome())
                .setUsuarioId(p.getUsuarioId())
                .addAllMusicaIds(p.getMusicaIds())
                .build();
    }

    @Override
    public void healthCheck(Empty request, StreamObserver<StatusResponse> responseObserver) {
        respond(responseObserver, () -> {
            Map<String, Object> info = service.healthCheck();
            return StatusResponse.newBuilder()
                    .setSucesso(Boolean.TRUE.equals(info.get("sucesso")))
                    .setMensagem(String.valueOf(info.get("mensagem")))
                    .build();
        });
    }

    @Override
    public void resetSeed(Empty request, StreamObserver<StatusResponse> responseObserver) {
        respond(responseObserver, () -> {
            Map<String, Object> info = service.resetSeed();
            return StatusResponse.newBuilder()
                    .setSucesso(Boolean.TRUE.equals(info.get("sucesso")))
                    .setMensagem(String.valueOf(info.get("mensagem")))
                    .build();
        });
    }

    @Override
    public void listarUsuarios(Empty request, StreamObserver<UsuarioListResponse> responseObserver) {
        respond(responseObserver, () -> {
            UsuarioListResponse.Builder builder = UsuarioListResponse.newBuilder();
            service.listarUsuarios().forEach(u -> builder.addUsuarios(toProto(u)));
            return builder.build();
        });
    }

    @Override
    public void obterUsuario(IdRequest request, StreamObserver<Usuario> responseObserver) {
        respond(responseObserver, () -> toProto(service.obterUsuario(request.getId())));
    }

    @Override
    public void criarUsuario(CriarUsuarioRequest request, StreamObserver<Usuario> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.criarUsuario(request.getNome(), request.getIdade(), request.getId().isBlank() ? null : request.getId())
        ));
    }

    @Override
    public void atualizarUsuario(AtualizarUsuarioRequest request, StreamObserver<Usuario> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.atualizarUsuario(request.getId(), request.getNome(), request.getIdade())
        ));
    }

    @Override
    public void removerUsuario(IdRequest request, StreamObserver<StatusResponse> responseObserver) {
        respond(responseObserver, () -> {
            boolean ok = service.removerUsuario(request.getId());
            return StatusResponse.newBuilder().setSucesso(ok).setMensagem("Usuário removido").build();
        });
    }

    @Override
    public void listarMusicas(Empty request, StreamObserver<MusicaListResponse> responseObserver) {
        respond(responseObserver, () -> {
            MusicaListResponse.Builder builder = MusicaListResponse.newBuilder();
            service.listarMusicas().forEach(m -> builder.addMusicas(toProto(m)));
            return builder.build();
        });
    }

    @Override
    public void obterMusica(IdRequest request, StreamObserver<Musica> responseObserver) {
        respond(responseObserver, () -> toProto(service.obterMusica(request.getId())));
    }

    @Override
    public void criarMusica(CriarMusicaRequest request, StreamObserver<Musica> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.criarMusica(request.getNome(), request.getArtista(), request.getId().isBlank() ? null : request.getId())
        ));
    }

    @Override
    public void atualizarMusica(AtualizarMusicaRequest request, StreamObserver<Musica> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.atualizarMusica(request.getId(), request.getNome(), request.getArtista())
        ));
    }

    @Override
    public void removerMusica(IdRequest request, StreamObserver<StatusResponse> responseObserver) {
        respond(responseObserver, () -> {
            boolean ok = service.removerMusica(request.getId());
            return StatusResponse.newBuilder().setSucesso(ok).setMensagem("Música removida").build();
        });
    }

    @Override
    public void listarPlaylists(Empty request, StreamObserver<PlaylistListResponse> responseObserver) {
        respond(responseObserver, () -> {
            PlaylistListResponse.Builder builder = PlaylistListResponse.newBuilder();
            service.listarPlaylists().forEach(p -> builder.addPlaylists(toProto(p)));
            return builder.build();
        });
    }

    @Override
    public void obterPlaylist(IdRequest request, StreamObserver<Playlist> responseObserver) {
        respond(responseObserver, () -> toProto(service.obterPlaylist(request.getId())));
    }

    @Override
    public void criarPlaylist(CriarPlaylistRequest request, StreamObserver<Playlist> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.criarPlaylist(
                        request.getNome(),
                        request.getUsuarioId(),
                        request.getMusicaIdsList(),
                        request.getId().isBlank() ? null : request.getId()
                )
        ));
    }

    @Override
    public void atualizarPlaylist(AtualizarPlaylistRequest request, StreamObserver<Playlist> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.atualizarPlaylist(
                        request.getId(),
                        request.getNome(),
                        request.getUsuarioId().isBlank() ? null : request.getUsuarioId(),
                        request.getMusicaIdsList()
                )
        ));
    }

    @Override
    public void removerPlaylist(IdRequest request, StreamObserver<StatusResponse> responseObserver) {
        respond(responseObserver, () -> {
            boolean ok = service.removerPlaylist(request.getId());
            return StatusResponse.newBuilder().setSucesso(ok).setMensagem("Playlist removida").build();
        });
    }

    @Override
    public void adicionarMusicaNaPlaylist(PlaylistMusicaRequest request, StreamObserver<Playlist> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.adicionarMusicaNaPlaylist(request.getPlaylistId(), request.getMusicaId())
        ));
    }

    @Override
    public void removerMusicaDaPlaylist(PlaylistMusicaRequest request, StreamObserver<Playlist> responseObserver) {
        respond(responseObserver, () -> toProto(
                service.removerMusicaDaPlaylist(request.getPlaylistId(), request.getMusicaId())
        ));
    }

    @Override
    public void listarPlaylistsPorUsuario(IdRequest request, StreamObserver<PlaylistListResponse> responseObserver) {
        respond(responseObserver, () -> {
            PlaylistListResponse.Builder builder = PlaylistListResponse.newBuilder();
            service.listarPlaylistsPorUsuario(request.getId()).forEach(p -> builder.addPlaylists(toProto(p)));
            return builder.build();
        });
    }

    @Override
    public void listarMusicasPorPlaylist(IdRequest request, StreamObserver<MusicaListResponse> responseObserver) {
        respond(responseObserver, () -> {
            MusicaListResponse.Builder builder = MusicaListResponse.newBuilder();
            service.listarMusicasPorPlaylist(request.getId()).forEach(m -> builder.addMusicas(toProto(m)));
            return builder.build();
        });
    }

    @Override
    public void listarPlaylistsPorMusica(IdRequest request, StreamObserver<PlaylistListResponse> responseObserver) {
        respond(responseObserver, () -> {
            PlaylistListResponse.Builder builder = PlaylistListResponse.newBuilder();
            service.listarPlaylistsPorMusica(request.getId()).forEach(p -> builder.addPlaylists(toProto(p)));
            return builder.build();
        });
    }
}
