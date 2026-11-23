package br.unifor.distribuidos.common.exception;

/**
 * Exceção lançada quando os parâmetros informados violam regras de validação.
 */
public class ValidationException extends RuntimeException {
    public ValidationException(String message) {
        super(message);
    }
}
