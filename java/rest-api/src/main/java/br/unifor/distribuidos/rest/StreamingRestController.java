package br.unifor.distribuidos.rest;

import br.unifor.distribuidos.common.exception.ResourceNotFoundException;
import br.unifor.distribuidos.common.exception.ValidationException;
import br.unifor.distribuidos.common.model.Musica;
import br.unifor.distribuidos.common.model.Playlist;
import br.unifor.distribuidos.common.model.Usuario;
import br.unifor.distribuidos.common.service.StreamingService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Entrega Java 1: API REST delegando ao núcleo compartilhado StreamingService.
 */
@RestController
public class StreamingRestController {
    private final StreamingService service;

    public StreamingRestController(StreamingService service) {
        this.service = service;
    }

    public record UsuarioInput(String id, String nome, int idade) {}
    public record MusicaInput(String id, String nome, String artista) {}
    public record PlaylistInput(String id, String nome, String usuarioId, List<String> musicaIds) {}

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, String>> handleNotFound(ResourceNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("erro", ex.getMessage()));
    }

    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<Map<String, String>> handleValidation(ValidationException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("erro", ex.getMessage()));
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return service.healthCheck();
    }

    @PostMapping("/reset")
    public Map<String, Object> reset() {
        return service.resetSeed();
    }

    // Usuários
    @GetMapping("/usuarios")
    public List<Usuario> listarUsuarios() {
        return service.listarUsuarios();
    }

    @GetMapping("/usuarios/{id}")
    public Usuario obterUsuario(@PathVariable String id) {
        return service.obterUsuario(id);
    }

    @PostMapping("/usuarios")
    @ResponseStatus(HttpStatus.CREATED)
    public Usuario criarUsuario(@RequestBody UsuarioInput input) {
        return service.criarUsuario(input.nome(), input.idade(), input.id());
    }

    @PutMapping("/usuarios/{id}")
    public Usuario atualizarUsuario(@PathVariable String id, @RequestBody UsuarioInput input) {
        return service.atualizarUsuario(id, input.nome(), input.idade());
    }

    @DeleteMapping("/usuarios/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void removerUsuario(@PathVariable String id) {
        service.removerUsuario(id);
    }

    @GetMapping("/usuarios/{id}/playlists")
    public List<Playlist> listarPlaylistsPorUsuario(@PathVariable String id) {
        return service.listarPlaylistsPorUsuario(id);
    }

    // Músicas
    @GetMapping("/musicas")
    public List<Musica> listarMusicas() {
        return service.listarMusicas();
    }

    @GetMapping("/musicas/{id}")
    public Musica obterMusica(@PathVariable String id) {
        return service.obterMusica(id);
    }

    @PostMapping("/musicas")
    @ResponseStatus(HttpStatus.CREATED)
    public Musica criarMusica(@RequestBody MusicaInput input) {
        return service.criarMusica(input.nome(), input.artista(), input.id());
    }

    @PutMapping("/musicas/{id}")
    public Musica atualizarMusica(@PathVariable String id, @RequestBody MusicaInput input) {
        return service.atualizarMusica(id, input.nome(), input.artista());
    }

    @DeleteMapping("/musicas/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void removerMusica(@PathVariable String id) {
        service.removerMusica(id);
    }

    @GetMapping("/musicas/{id}/playlists")
    public List<Playlist> listarPlaylistsPorMusica(@PathVariable String id) {
        return service.listarPlaylistsPorMusica(id);
    }

    // Playlists
    @GetMapping("/playlists")
    public List<Playlist> listarPlaylists() {
        return service.listarPlaylists();
    }

    @GetMapping("/playlists/{id}")
    public Playlist obterPlaylist(@PathVariable String id) {
        return service.obterPlaylist(id);
    }

    @PostMapping("/playlists")
    @ResponseStatus(HttpStatus.CREATED)
    public Playlist criarPlaylist(@RequestBody PlaylistInput input) {
        return service.criarPlaylist(input.nome(), input.usuarioId(), input.musicaIds(), input.id());
    }

    @PutMapping("/playlists/{id}")
    public Playlist atualizarPlaylist(@PathVariable String id, @RequestBody PlaylistInput input) {
        return service.atualizarPlaylist(id, input.nome(), input.usuarioId(), input.musicaIds());
    }

    @DeleteMapping("/playlists/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void removerPlaylist(@PathVariable String id) {
        service.removerPlaylist(id);
    }

    @GetMapping("/playlists/{id}/musicas")
    public List<Musica> listarMusicasPorPlaylist(@PathVariable String id) {
        return service.listarMusicasPorPlaylist(id);
    }

    @PostMapping("/playlists/{id}/musicas/{musicaId}")
    public Playlist adicionarMusicaNaPlaylist(@PathVariable String id, @PathVariable String musicaId) {
        return service.adicionarMusicaNaPlaylist(id, musicaId);
    }

    @DeleteMapping("/playlists/{id}/musicas/{musicaId}")
    public Playlist removerMusicaDaPlaylist(@PathVariable String id, @PathVariable String musicaId) {
        return service.removerMusicaDaPlaylist(id, musicaId);
    }
}
