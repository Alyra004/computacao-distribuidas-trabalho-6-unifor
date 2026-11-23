package br.unifor.distribuidos.common;

import br.unifor.distribuidos.common.exception.ResourceNotFoundException;
import br.unifor.distribuidos.common.exception.ValidationException;
import br.unifor.distribuidos.common.model.Playlist;
import br.unifor.distribuidos.common.repository.InMemoryStreamingRepository;
import br.unifor.distribuidos.common.service.StreamingService;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class StreamingServiceTest {

    @Test
    void seedPadraoEConsultasObrigatorias() {
        StreamingService service = new StreamingService();
        assertEquals(10, service.listarUsuarios().size());
        assertEquals(20, service.listarMusicas().size());
        assertEquals(15, service.listarPlaylists().size());

        assertFalse(service.listarPlaylistsPorUsuario("u1").isEmpty());
        assertFalse(service.listarMusicasPorPlaylist("p1").isEmpty());
        assertFalse(service.listarPlaylistsPorMusica("m1").isEmpty());
    }

    @Test
    void seedLargeEIndicesInvertidos() {
        Path largeSeed = Path.of("..", "..", "contracts", "seed", "seed_large.json");
        if (!Files.isRegularFile(largeSeed)) {
            largeSeed = Path.of("..", "contracts", "seed", "seed_large.json");
        }
        if (!Files.isRegularFile(largeSeed)) {
            largeSeed = Path.of("contracts", "seed", "seed_large.json");
        }
        Assumptions.assumeTrue(Files.isRegularFile(largeSeed), "seed_large.json ainda não gerado.");

        StreamingService largeService = new StreamingService(new InMemoryStreamingRepository(largeSeed));
        assertEquals(50, largeService.listarUsuarios().size());
        assertEquals(500, largeService.listarMusicas().size());
        assertEquals(50, largeService.listarPlaylists().size());
        assertEquals(200, largeService.listarMusicasPorPlaylist("p1").size());

        String primeiraMusica = largeService.obterPlaylist("p1").getMusicaIds().get(0);
        assertTrue(largeService.listarPlaylistsPorMusica(primeiraMusica).stream()
                .anyMatch(p -> "p1".equals(p.getId())));

        largeService.removerMusicaDaPlaylist("p1", primeiraMusica);
        assertFalse(largeService.listarPlaylistsPorMusica(primeiraMusica).stream()
                .anyMatch(p -> "p1".equals(p.getId())));
    }

    @Test
    void crudEIntegridadeRelacional() {
        StreamingService service = new StreamingService();
        var user = service.criarUsuario("Teste", 25, "u_test");
        assertEquals("u_test", user.getId());

        var song = service.criarMusica("Som Teste", "Artista Teste", "m_test");
        Playlist pl = service.criarPlaylist("Playlist Teste", "u_test", List.of(song.getId()), "p_test");
        assertEquals(1, service.listarMusicasPorPlaylist(pl.getId()).size());
        assertEquals(List.of("p_test"), service.listarPlaylistsPorMusica(song.getId()).stream().map(Playlist::getId).toList());

        service.atualizarPlaylist("p_test", "Playlist Editada", null, List.of("m1"));
        assertTrue(service.listarPlaylistsPorMusica(song.getId()).isEmpty());
        assertTrue(service.listarPlaylistsPorMusica("m1").stream().anyMatch(p -> "p_test".equals(p.getId())));

        service.adicionarMusicaNaPlaylist("p_test", song.getId());
        service.removerMusica(song.getId());
        assertEquals(1, service.listarMusicasPorPlaylist("p_test").size());

        service.removerUsuario("u_test");
        assertThrows(ResourceNotFoundException.class, () -> service.obterPlaylist("p_test"));
        assertFalse(service.listarPlaylistsPorMusica("m1").stream().anyMatch(p -> "p_test".equals(p.getId())));
    }

    @Test
    void validacoes() {
        StreamingService service = new StreamingService();
        assertThrows(ValidationException.class, () -> service.criarUsuario("   ", 20, null));
        assertThrows(ResourceNotFoundException.class, () -> service.obterUsuario("inexistente"));
    }
}
