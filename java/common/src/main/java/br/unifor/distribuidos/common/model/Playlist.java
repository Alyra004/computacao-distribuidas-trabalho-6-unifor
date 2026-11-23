package br.unifor.distribuidos.common.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Representa uma playlist pertencente a um usuário e associada a músicas.
 */
public class Playlist {
    private String id;
    private String nome;
    private String usuarioId;
    private List<String> musicaIds = new ArrayList<>();

    public Playlist() {
    }

    public Playlist(String id, String nome, String usuarioId, List<String> musicaIds) {
        this.id = id;
        this.nome = nome;
        this.usuarioId = usuarioId;
        this.musicaIds = musicaIds != null ? new ArrayList<>(musicaIds) : new ArrayList<>();
    }

    public Playlist(Playlist other) {
        this(other.id, other.nome, other.usuarioId, other.musicaIds);
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public String getUsuarioId() {
        return usuarioId;
    }

    public void setUsuarioId(String usuarioId) {
        this.usuarioId = usuarioId;
    }

    public List<String> getMusicaIds() {
        return musicaIds;
    }

    public void setMusicaIds(List<String> musicaIds) {
        this.musicaIds = musicaIds != null ? new ArrayList<>(musicaIds) : new ArrayList<>();
    }
}
