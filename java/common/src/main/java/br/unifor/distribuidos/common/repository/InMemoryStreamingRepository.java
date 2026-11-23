package br.unifor.distribuidos.common.repository;

import br.unifor.distribuidos.common.model.Musica;
import br.unifor.distribuidos.common.model.Playlist;
import br.unifor.distribuidos.common.model.Usuario;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 * Repositório em memória thread-safe com carga determinística e índices invertidos O(1)/O(K).
 */
public class InMemoryStreamingRepository {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    private final Map<String, Usuario> usuarios = new LinkedHashMap<>();
    private final Map<String, Musica> musicas = new LinkedHashMap<>();
    private final Map<String, Playlist> playlists = new LinkedHashMap<>();
    private final Map<String, Set<String>> usuarioPlaylists = new LinkedHashMap<>();
    private final Map<String, Set<String>> musicaPlaylists = new LinkedHashMap<>();
    private final Path customSeedPath;

    public InMemoryStreamingRepository() {
        this(null);
    }

    public InMemoryStreamingRepository(Path customSeedPath) {
        this.customSeedPath = customSeedPath;
        resetSeed();
    }

    public ReentrantReadWriteLock getLock() {
        return lock;
    }

    public Map<String, Usuario> getUsuariosMap() {
        return usuarios;
    }

    public Map<String, Musica> getMusicasMap() {
        return musicas;
    }

    public Map<String, Playlist> getPlaylistsMap() {
        return playlists;
    }

    public Map<String, Set<String>> getUsuarioPlaylistsIndex() {
        return usuarioPlaylists;
    }

    public Map<String, Set<String>> getMusicaPlaylistsIndex() {
        return musicaPlaylists;
    }

    public final void resetSeed() {
        Path resolved = resolveSeedPath();
        lock.writeLock().lock();
        try {
            usuarios.clear();
            musicas.clear();
            playlists.clear();
            usuarioPlaylists.clear();
            musicaPlaylists.clear();

            if (resolved != null) {
                loadFromJson(resolved);
            } else {
                loadFallbackSeed();
            }
        } finally {
            lock.writeLock().unlock();
        }
    }

    private Path resolveSeedPath() {
        List<Path> candidates = new ArrayList<>();
        if (customSeedPath != null) {
            candidates.add(customSeedPath);
        }
        String envPath = System.getenv("SEED_DATA_PATH");
        if (envPath != null && !envPath.isBlank()) {
            candidates.add(Path.of(envPath));
        }
        candidates.add(Path.of("contracts", "seed", "initial_data.json"));
        candidates.add(Path.of("..", "contracts", "seed", "initial_data.json"));
        candidates.add(Path.of("..", "..", "contracts", "seed", "initial_data.json"));

        for (Path candidate : candidates) {
            if (Files.isRegularFile(candidate)) {
                return candidate;
            }
        }
        return null;
    }

    private void indexPlaylist(Playlist playlist) {
        usuarioPlaylists
                .computeIfAbsent(playlist.getUsuarioId(), k -> new LinkedHashSet<>())
                .add(playlist.getId());
        for (String mid : playlist.getMusicaIds()) {
            musicaPlaylists
                    .computeIfAbsent(mid, k -> new LinkedHashSet<>())
                    .add(playlist.getId());
        }
    }

    private void loadFromJson(Path path) {
        try {
            JsonNode root = OBJECT_MAPPER.readTree(path.toFile());
            for (JsonNode node : root.path("usuarios")) {
                Usuario u = new Usuario(
                        node.path("id").asText(),
                        node.path("nome").asText(),
                        node.path("idade").asInt()
                );
                usuarios.put(u.getId(), u);
                usuarioPlaylists.put(u.getId(), new LinkedHashSet<>());
            }
            for (JsonNode node : root.path("musicas")) {
                Musica m = new Musica(
                        node.path("id").asText(),
                        node.path("nome").asText(),
                        node.path("artista").asText()
                );
                musicas.put(m.getId(), m);
                musicaPlaylists.put(m.getId(), new LinkedHashSet<>());
            }
            for (JsonNode node : root.path("playlists")) {
                Set<String> uniqueIds = new LinkedHashSet<>();
                for (JsonNode mid : node.path("musicaIds")) {
                    uniqueIds.add(mid.asText());
                }
                Playlist p = new Playlist(
                        node.path("id").asText(),
                        node.path("nome").asText(),
                        node.path("usuarioId").asText(),
                        new ArrayList<>(uniqueIds)
                );
                playlists.put(p.getId(), p);
                indexPlaylist(p);
            }
        } catch (IOException ex) {
            usuarios.clear();
            musicas.clear();
            playlists.clear();
            usuarioPlaylists.clear();
            musicaPlaylists.clear();
            loadFallbackSeed();
        }
    }

    private void loadFallbackSeed() {
        usuarios.put("u1", new Usuario("u1", "Amanda Lira", 22));
        usuarios.put("u2", new Usuario("u2", "João Igor", 23));
        usuarios.put("u3", new Usuario("u3", "Raquel Quirino", 22));
        usuarios.keySet().forEach(uid -> usuarioPlaylists.put(uid, new LinkedHashSet<>()));

        musicas.put("m1", new Musica("m1", "Evidências", "Chitãozinho & Xororó"));
        musicas.put("m2", new Musica("m2", "Águas de Março", "Elis Regina & Tom Jobim"));
        musicas.put("m3", new Musica("m3", "Tempo Perdido", "Legião Urbana"));
        musicas.keySet().forEach(mid -> musicaPlaylists.put(mid, new LinkedHashSet<>()));

        Playlist p1 = new Playlist("p1", "Clássicos Brasileiros", "u1", List.of("m1", "m2"));
        Playlist p2 = new Playlist("p2", "Rock Nacional", "u2", List.of("m3"));
        playlists.put("p1", p1);
        playlists.put("p2", p2);
        indexPlaylist(p1);
        indexPlaylist(p2);
    }
}
