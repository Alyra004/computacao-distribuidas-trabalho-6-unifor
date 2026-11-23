package br.unifor.distribuidos.graphql;

import br.unifor.distribuidos.common.exception.ResourceNotFoundException;
import br.unifor.distribuidos.common.model.Musica;
import br.unifor.distribuidos.common.model.Playlist;
import br.unifor.distribuidos.common.model.Usuario;
import br.unifor.distribuidos.common.service.StreamingService;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.MutationMapping;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.graphql.data.method.annotation.SchemaMapping;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;
import java.util.Map;

/**
 * Entrega Java 3: API GraphQL delegando ao núcleo StreamingService.
 */
@Controller
public class StreamingGraphqlController {
    private final StreamingService service;

    public StreamingGraphqlController(StreamingService service) {
        this.service = service;
    }

    public record StatusResponse(boolean sucesso, String mensagem) {}

    @GetMapping("/health")
    @ResponseBody
    public Map<String, Object> httpHealth() {
        return service.healthCheck();
    }

    @QueryMapping
    public StatusResponse health() {
        Map<String, Object> info = service.healthCheck();
        return new StatusResponse(Boolean.TRUE.equals(info.get("sucesso")), String.valueOf(info.get("mensagem")));
    }

    @QueryMapping
    public List<Usuario> usuarios() {
        return service.listarUsuarios();
    }

    @QueryMapping
    public Usuario usuario(@Argument String id) {
        try {
            return service.obterUsuario(id);
        } catch (ResourceNotFoundException ex) {
            return null;
        }
    }

    @QueryMapping
    public List<Musica> musicas() {
        return service.listarMusicas();
    }

    @QueryMapping
    public Musica musica(@Argument String id) {
        try {
            return service.obterMusica(id);
        } catch (ResourceNotFoundException ex) {
            return null;
        }
    }

    @QueryMapping
    public List<Playlist> playlists() {
        return service.listarPlaylists();
    }

    @QueryMapping
    public Playlist playlist(@Argument String id) {
        try {
            return service.obterPlaylist(id);
        } catch (ResourceNotFoundException ex) {
            return null;
        }
    }

    @QueryMapping
    public List<Playlist> playlistsPorUsuario(@Argument String usuarioId) {
        return service.listarPlaylistsPorUsuario(usuarioId);
    }

    @QueryMapping
    public List<Musica> musicasPorPlaylist(@Argument String playlistId) {
        return service.listarMusicasPorPlaylist(playlistId);
    }

    @QueryMapping
    public List<Playlist> playlistsPorMusica(@Argument String musicaId) {
        return service.listarPlaylistsPorMusica(musicaId);
    }

    @SchemaMapping(typeName = "Usuario", field = "playlists")
    public List<Playlist> usuarioPlaylists(Usuario usuario) {
        return service.listarPlaylistsPorUsuario(usuario.getId());
    }

    @SchemaMapping(typeName = "Musica", field = "playlists")
    public List<Playlist> musicaPlaylists(Musica musica) {
        return service.listarPlaylistsPorMusica(musica.getId());
    }

    @SchemaMapping(typeName = "Playlist", field = "usuario")
    public Usuario playlistUsuario(Playlist playlist) {
        try {
            return service.obterUsuario(playlist.getUsuarioId());
        } catch (ResourceNotFoundException ex) {
            return null;
        }
    }

    @SchemaMapping(typeName = "Playlist", field = "musicas")
    public List<Musica> playlistMusicas(Playlist playlist) {
        return service.listarMusicasPorPlaylist(playlist.getId());
    }

    @MutationMapping
    public StatusResponse resetSeed() {
        Map<String, Object> info = service.resetSeed();
        return new StatusResponse(Boolean.TRUE.equals(info.get("sucesso")), String.valueOf(info.get("mensagem")));
    }

    @MutationMapping
    public Usuario criarUsuario(@Argument String nome, @Argument int idade, @Argument String id) {
        return service.criarUsuario(nome, idade, id);
    }

    @MutationMapping
    public Usuario atualizarUsuario(@Argument String id, @Argument String nome, @Argument int idade) {
        return service.atualizarUsuario(id, nome, idade);
    }

    @MutationMapping
    public boolean removerUsuario(@Argument String id) {
        return service.removerUsuario(id);
    }

    @MutationMapping
    public Musica criarMusica(@Argument String nome, @Argument String artista, @Argument String id) {
        return service.criarMusica(nome, artista, id);
    }

    @MutationMapping
    public Musica atualizarMusica(@Argument String id, @Argument String nome, @Argument String artista) {
        return service.atualizarMusica(id, nome, artista);
    }

    @MutationMapping
    public boolean removerMusica(@Argument String id) {
        return service.removerMusica(id);
    }

    @MutationMapping
    public Playlist criarPlaylist(@Argument String nome, @Argument String usuarioId, @Argument List<String> musicaIds, @Argument String id) {
        return service.criarPlaylist(nome, usuarioId, musicaIds, id);
    }

    @MutationMapping
    public Playlist atualizarPlaylist(@Argument String id, @Argument String nome, @Argument String usuarioId, @Argument List<String> musicaIds) {
        return service.atualizarPlaylist(id, nome, usuarioId, musicaIds);
    }

    @MutationMapping
    public boolean removerPlaylist(@Argument String id) {
        return service.removerPlaylist(id);
    }

    @MutationMapping
    public Playlist adicionarMusicaNaPlaylist(@Argument String playlistId, @Argument String musicaId) {
        return service.adicionarMusicaNaPlaylist(playlistId, musicaId);
    }

    @MutationMapping
    public Playlist removerMusicaDaPlaylist(@Argument String playlistId, @Argument String musicaId) {
        return service.removerMusicaDaPlaylist(playlistId, musicaId);
    }
}
