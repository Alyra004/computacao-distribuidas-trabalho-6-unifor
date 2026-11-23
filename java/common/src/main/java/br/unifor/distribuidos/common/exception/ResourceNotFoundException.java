package br.unifor.distribuidos.common.exception;

/**
 * Exceção lançada quando um recurso (Usuário, Música ou Playlist) não é encontrado.
 */
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
