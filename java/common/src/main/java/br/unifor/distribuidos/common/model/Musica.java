package br.unifor.distribuidos.common.model;

/**
 * Representa uma música mantida no catálogo do serviço.
 */
public class Musica {
    private String id;
    private String nome;
    private String artista;

    public Musica() {
    }

    public Musica(String id, String nome, String artista) {
        this.id = id;
        this.nome = nome;
        this.artista = artista;
    }

    public Musica(Musica other) {
        this(other.id, other.nome, other.artista);
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

    public String getArtista() {
        return artista;
    }

    public void setArtista(String artista) {
        this.artista = artista;
    }
}
