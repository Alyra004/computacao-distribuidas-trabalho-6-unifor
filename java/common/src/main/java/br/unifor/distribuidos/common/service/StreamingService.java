package br.unifor.distribuidos.common.service;

import br.unifor.distribuidos.common.exception.ResourceNotFoundException;
import br.unifor.distribuidos.common.exception.ValidationException;
import br.unifor.distribuidos.common.model.Musica;
import br.unifor.distribuidos.common.model.Playlist;
import br.unifor.distribuidos.common.model.Usuario;
import br.unifor.distribuidos.common.repository.InMemoryStreamingRepository;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Camada de serviço compartilhada entre todas as APIs Java (REST, SOAP, GraphQL e gRPC).
 */
public class StreamingService {
    private final InMemoryStreamingRepository repo;

    public StreamingService() {
        this(new InMemoryStreamingRepository());
    }

    public StreamingService(InMemoryStreamingRepository repo) {
        this.repo = repo;
    }

    public Map<String, Object> healthCheck() {
        repo.getLock().readLock().lock();
        try {
            Map<String, Object> status = new LinkedHashMap<>();
            status.put("sucesso", true);
            status.put("mensagem", "Serviço operacional");
            status.put("usuarios", repo.getUsuariosMap().size());
            status.put("musicas", repo.getMusicasMap().size());
            status.put("playlists", repo.getPlaylistsMap().size());
            return status;
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Map<String, Object> resetSeed() {
        repo.resetSeed();
        return Map.of("sucesso", true, "mensagem", "Dados iniciais restaurados");
    }

    // =========================================================================
    // Usuários (CRUD)
    // =========================================================================

    public List<Usuario> listarUsuarios() {
        repo.getLock().readLock().lock();
        try {
            return repo.getUsuariosMap().values().stream().map(Usuario::new).toList();
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Usuario obterUsuario(String usuarioId) {
        repo.getLock().readLock().lock();
        try {
            Usuario usuario = repo.getUsuariosMap().get(usuarioId);
            if (usuario == null) {
                throw new ResourceNotFoundException("Usuário '" + usuarioId + "' não encontrado.");
            }
            return new Usuario(usuario);
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Usuario criarUsuario(String nome, int idade, String id) {
        String nomeLimpo = nome == null ? "" : nome.trim();
        if (nomeLimpo.isEmpty()) {
            throw new ValidationException("O nome do usuário não pode ser vazio.");
        }
        if (idade < 0) {
            throw new ValidationException("A idade do usuário deve ser não negativa.");
        }

        repo.getLock().writeLock().lock();
        try {
            String novoId = (id != null && !id.isBlank()) ? id.trim() : "u-" + UUID.randomUUID().toString().substring(0, 8);
            if (repo.getUsuariosMap().containsKey(novoId)) {
                throw new ValidationException("Usuário com id '" + novoId + "' já existe.");
            }
            Usuario usuario = new Usuario(novoId, nomeLimpo, idade);
            repo.getUsuariosMap().put(novoId, usuario);
            repo.getUsuarioPlaylistsIndex().put(novoId, new LinkedHashSet<>());
            return new Usuario(usuario);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public Usuario atualizarUsuario(String usuarioId, String nome, int idade) {
        String nomeLimpo = nome == null ? "" : nome.trim();
        if (nomeLimpo.isEmpty()) {
            throw new ValidationException("O nome do usuário não pode ser vazio.");
        }
        if (idade < 0) {
            throw new ValidationException("A idade do usuário deve ser não negativa.");
        }

        repo.getLock().writeLock().lock();
        try {
            Usuario usuario = repo.getUsuariosMap().get(usuarioId);
            if (usuario == null) {
                throw new ResourceNotFoundException("Usuário '" + usuarioId + "' não encontrado.");
            }
            usuario.setNome(nomeLimpo);
            usuario.setIdade(idade);
            return new Usuario(usuario);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public boolean removerUsuario(String usuarioId) {
        repo.getLock().writeLock().lock();
        try {
            if (repo.getUsuariosMap().remove(usuarioId) == null) {
                throw new ResourceNotFoundException("Usuário '" + usuarioId + "' não encontrado.");
            }
            Set<String> playlistsDoUsuario = repo.getUsuarioPlaylistsIndex().remove(usuarioId);
            if (playlistsDoUsuario != null) {
                for (String pid : playlistsDoUsuario) {
                    Playlist removed = repo.getPlaylistsMap().remove(pid);
                    if (removed != null) {
                        for (String mid : removed.getMusicaIds()) {
                            Set<String> musicIdx = repo.getMusicaPlaylistsIndex().get(mid);
                            if (musicIdx != null) {
                                musicIdx.remove(pid);
                            }
                        }
                    }
                }
            }
            return true;
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    // =========================================================================
    // Músicas (CRUD)
    // =========================================================================

    public List<Musica> listarMusicas() {
        repo.getLock().readLock().lock();
        try {
            return repo.getMusicasMap().values().stream().map(Musica::new).toList();
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Musica obterMusica(String musicaId) {
        repo.getLock().readLock().lock();
        try {
            Musica musica = repo.getMusicasMap().get(musicaId);
            if (musica == null) {
                throw new ResourceNotFoundException("Música '" + musicaId + "' não encontrada.");
            }
            return new Musica(musica);
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Musica criarMusica(String nome, String artista, String id) {
        String nomeLimpo = nome == null ? "" : nome.trim();
        String artistaLimpo = artista == null ? "" : artista.trim();
        if (nomeLimpo.isEmpty() || artistaLimpo.isEmpty()) {
            throw new ValidationException("Nome e artista da música são obrigatórios.");
        }

        repo.getLock().writeLock().lock();
        try {
            String novoId = (id != null && !id.isBlank()) ? id.trim() : "m-" + UUID.randomUUID().toString().substring(0, 8);
            if (repo.getMusicasMap().containsKey(novoId)) {
                throw new ValidationException("Música com id '" + novoId + "' já existe.");
            }
            Musica musica = new Musica(novoId, nomeLimpo, artistaLimpo);
            repo.getMusicasMap().put(novoId, musica);
            repo.getMusicaPlaylistsIndex().put(novoId, new LinkedHashSet<>());
            return new Musica(musica);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public Musica atualizarMusica(String musicaId, String nome, String artista) {
        String nomeLimpo = nome == null ? "" : nome.trim();
        String artistaLimpo = artista == null ? "" : artista.trim();
        if (nomeLimpo.isEmpty() || artistaLimpo.isEmpty()) {
            throw new ValidationException("Nome e artista da música são obrigatórios.");
        }

        repo.getLock().writeLock().lock();
        try {
            Musica musica = repo.getMusicasMap().get(musicaId);
            if (musica == null) {
                throw new ResourceNotFoundException("Música '" + musicaId + "' não encontrada.");
            }
            musica.setNome(nomeLimpo);
            musica.setArtista(artistaLimpo);
            return new Musica(musica);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public boolean removerMusica(String musicaId) {
        repo.getLock().writeLock().lock();
        try {
            if (repo.getMusicasMap().remove(musicaId) == null) {
                throw new ResourceNotFoundException("Música '" + musicaId + "' não encontrada.");
            }
            Set<String> playlistsDaMusica = repo.getMusicaPlaylistsIndex().remove(musicaId);
            if (playlistsDaMusica != null) {
                for (String pid : playlistsDaMusica) {
                    Playlist playlist = repo.getPlaylistsMap().get(pid);
                    if (playlist != null) {
                        playlist.getMusicaIds().removeIf(musicaId::equals);
                    }
                }
            }
            return true;
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    // =========================================================================
    // Playlists (CRUD + Associação)
    // =========================================================================

    private List<String> validarMusicas(List<String> musicaIds) {
        Set<String> unicos = new LinkedHashSet<>();
        if (musicaIds != null) {
            for (String mid : musicaIds) {
                if (!repo.getMusicasMap().containsKey(mid)) {
                    throw new ResourceNotFoundException("Música '" + mid + "' não encontrada.");
                }
                unicos.add(mid);
            }
        }
        return new ArrayList<>(unicos);
    }

    public List<Playlist> listarPlaylists() {
        repo.getLock().readLock().lock();
        try {
            return repo.getPlaylistsMap().values().stream().map(Playlist::new).toList();
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Playlist obterPlaylist(String playlistId) {
        repo.getLock().readLock().lock();
        try {
            Playlist playlist = repo.getPlaylistsMap().get(playlistId);
            if (playlist == null) {
                throw new ResourceNotFoundException("Playlist '" + playlistId + "' não encontrada.");
            }
            return new Playlist(playlist);
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public Playlist criarPlaylist(String nome, String usuarioId, List<String> musicaIds, String id) {
        String nomeLimpo = nome == null ? "" : nome.trim();
        if (nomeLimpo.isEmpty()) {
            throw new ValidationException("O nome da playlist não pode ser vazio.");
        }

        repo.getLock().writeLock().lock();
        try {
            if (!repo.getUsuariosMap().containsKey(usuarioId)) {
                throw new ResourceNotFoundException("Usuário '" + usuarioId + "' não encontrado.");
            }
            List<String> musicasValidadas = validarMusicas(musicaIds);
            String novoId = (id != null && !id.isBlank()) ? id.trim() : "p-" + UUID.randomUUID().toString().substring(0, 8);
            if (repo.getPlaylistsMap().containsKey(novoId)) {
                throw new ValidationException("Playlist com id '" + novoId + "' já existe.");
            }
            Playlist playlist = new Playlist(novoId, nomeLimpo, usuarioId, musicasValidadas);
            repo.getPlaylistsMap().put(novoId, playlist);
            repo.getUsuarioPlaylistsIndex().computeIfAbsent(usuarioId, k -> new LinkedHashSet<>()).add(novoId);
            for (String mid : musicasValidadas) {
                repo.getMusicaPlaylistsIndex().computeIfAbsent(mid, k -> new LinkedHashSet<>()).add(novoId);
            }
            return new Playlist(playlist);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public Playlist atualizarPlaylist(String playlistId, String nome, String usuarioId, List<String> musicaIds) {
        String nomeLimpo = nome == null ? "" : nome.trim();
        if (nomeLimpo.isEmpty()) {
            throw new ValidationException("O nome da playlist não pode ser vazio.");
        }

        repo.getLock().writeLock().lock();
        try {
            Playlist playlist = repo.getPlaylistsMap().get(playlistId);
            if (playlist == null) {
                throw new ResourceNotFoundException("Playlist '" + playlistId + "' não encontrada.");
            }
            if (usuarioId != null && !usuarioId.isBlank() && !usuarioId.equals(playlist.getUsuarioId())) {
                if (!repo.getUsuariosMap().containsKey(usuarioId)) {
                    throw new ResourceNotFoundException("Usuário '" + usuarioId + "' não encontrado.");
                }
                Set<String> oldUserIdx = repo.getUsuarioPlaylistsIndex().get(playlist.getUsuarioId());
                if (oldUserIdx != null) {
                    oldUserIdx.remove(playlistId);
                }
                repo.getUsuarioPlaylistsIndex().computeIfAbsent(usuarioId, k -> new LinkedHashSet<>()).add(playlistId);
                playlist.setUsuarioId(usuarioId);
            }
            if (musicaIds != null) {
                List<String> novasMusicas = validarMusicas(musicaIds);
                for (String oldMid : playlist.getMusicaIds()) {
                    Set<String> oldMusicIdx = repo.getMusicaPlaylistsIndex().get(oldMid);
                    if (oldMusicIdx != null) {
                        oldMusicIdx.remove(playlistId);
                    }
                }
                for (String newMid : novasMusicas) {
                    repo.getMusicaPlaylistsIndex().computeIfAbsent(newMid, k -> new LinkedHashSet<>()).add(playlistId);
                }
                playlist.setMusicaIds(novasMusicas);
            }
            playlist.setNome(nomeLimpo);
            return new Playlist(playlist);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public boolean removerPlaylist(String playlistId) {
        repo.getLock().writeLock().lock();
        try {
            Playlist removed = repo.getPlaylistsMap().remove(playlistId);
            if (removed == null) {
                throw new ResourceNotFoundException("Playlist '" + playlistId + "' não encontrada.");
            }
            Set<String> userIdx = repo.getUsuarioPlaylistsIndex().get(removed.getUsuarioId());
            if (userIdx != null) {
                userIdx.remove(playlistId);
            }
            for (String mid : removed.getMusicaIds()) {
                Set<String> musicIdx = repo.getMusicaPlaylistsIndex().get(mid);
                if (musicIdx != null) {
                    musicIdx.remove(playlistId);
                }
            }
            return true;
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public Playlist adicionarMusicaNaPlaylist(String playlistId, String musicaId) {
        repo.getLock().writeLock().lock();
        try {
            Playlist playlist = repo.getPlaylistsMap().get(playlistId);
            if (playlist == null) {
                throw new ResourceNotFoundException("Playlist '" + playlistId + "' não encontrada.");
            }
            if (!repo.getMusicasMap().containsKey(musicaId)) {
                throw new ResourceNotFoundException("Música '" + musicaId + "' não encontrada.");
            }
            Set<String> musicIdx = repo.getMusicaPlaylistsIndex().computeIfAbsent(musicaId, k -> new LinkedHashSet<>());
            if (musicIdx.add(playlistId)) {
                playlist.getMusicaIds().add(musicaId);
            }
            return new Playlist(playlist);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    public Playlist removerMusicaDaPlaylist(String playlistId, String musicaId) {
        repo.getLock().writeLock().lock();
        try {
            Playlist playlist = repo.getPlaylistsMap().get(playlistId);
            if (playlist == null) {
                throw new ResourceNotFoundException("Playlist '" + playlistId + "' não encontrada.");
            }
            if (!repo.getMusicasMap().containsKey(musicaId)) {
                throw new ResourceNotFoundException("Música '" + musicaId + "' não encontrada.");
            }
            playlist.getMusicaIds().removeIf(musicaId::equals);
            Set<String> musicIdx = repo.getMusicaPlaylistsIndex().get(musicaId);
            if (musicIdx != null) {
                musicIdx.remove(playlistId);
            }
            return new Playlist(playlist);
        } finally {
            repo.getLock().writeLock().unlock();
        }
    }

    // =========================================================================
    // Consultas Relacionais Obrigatórias (Slide 6)
    // =========================================================================

    public List<Playlist> listarPlaylistsPorUsuario(String usuarioId) {
        repo.getLock().readLock().lock();
        try {
            if (!repo.getUsuariosMap().containsKey(usuarioId)) {
                throw new ResourceNotFoundException("Usuário '" + usuarioId + "' não encontrado.");
            }
            Set<String> pids = repo.getUsuarioPlaylistsIndex().getOrDefault(usuarioId, Collections.emptySet());
            List<Playlist> resultado = new ArrayList<>(pids.size());
            for (String pid : pids) {
                Playlist p = repo.getPlaylistsMap().get(pid);
                if (p != null) {
                    resultado.add(new Playlist(p));
                }
            }
            return resultado;
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public List<Musica> listarMusicasPorPlaylist(String playlistId) {
        repo.getLock().readLock().lock();
        try {
            Playlist playlist = repo.getPlaylistsMap().get(playlistId);
            if (playlist == null) {
                throw new ResourceNotFoundException("Playlist '" + playlistId + "' não encontrada.");
            }
            List<Musica> resultado = new ArrayList<>(playlist.getMusicaIds().size());
            for (String mid : playlist.getMusicaIds()) {
                Musica m = repo.getMusicasMap().get(mid);
                if (m != null) {
                    resultado.add(new Musica(m));
                }
            }
            return resultado;
        } finally {
            repo.getLock().readLock().unlock();
        }
    }

    public List<Playlist> listarPlaylistsPorMusica(String musicaId) {
        repo.getLock().readLock().lock();
        try {
            if (!repo.getMusicasMap().containsKey(musicaId)) {
                throw new ResourceNotFoundException("Música '" + musicaId + "' não encontrada.");
            }
            Set<String> pids = repo.getMusicaPlaylistsIndex().getOrDefault(musicaId, Collections.emptySet());
            List<Playlist> resultado = new ArrayList<>(pids.size());
            for (String pid : pids) {
                Playlist p = repo.getPlaylistsMap().get(pid);
                if (p != null) {
                    resultado.add(new Playlist(p));
                }
            }
            return resultado;
        } finally {
            repo.getLock().readLock().unlock();
        }
    }
}
