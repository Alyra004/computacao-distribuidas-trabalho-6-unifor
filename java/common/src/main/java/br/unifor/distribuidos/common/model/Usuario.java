package br.unifor.distribuidos.common.model;

/**
 * Representa um usuário do serviço de streaming.
 */
public class Usuario {
    private String id;
    private String nome;
    private int idade;

    public Usuario() {
    }

    public Usuario(String id, String nome, int idade) {
        this.id = id;
        this.nome = nome;
        this.idade = idade;
    }

    public Usuario(Usuario other) {
        this(other.id, other.nome, other.idade);
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

    public int getIdade() {
        return idade;
    }

    public void setIdade(int idade) {
        this.idade = idade;
    }
}
