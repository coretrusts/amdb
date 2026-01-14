/**
 * AmDb Java异常类
 */
package com.amdb;

public class AmDbException extends Exception {
    public AmDbException(String message) {
        super(message);
    }
    
    public AmDbException(String message, Throwable cause) {
        super(message, cause);
    }
}

