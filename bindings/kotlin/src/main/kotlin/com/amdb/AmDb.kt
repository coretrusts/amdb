/**
 * AmDb Kotlin绑定
 * 使用JNI调用C API
 */

package com.amdb

class AmDb private constructor(private val handle: Long) {
    companion object {
        init {
            System.loadLibrary("amdb_jni")
        }
        
        @JvmStatic
        external fun nativeInit(dataDir: String): Long
        
        @JvmStatic
        external fun nativeClose(handle: Long)
        
        @JvmStatic
        external fun nativePut(handle: Long, key: ByteArray, value: ByteArray): ByteArray
        
        @JvmStatic
        external fun nativeGet(handle: Long, key: ByteArray, version: Int): ByteArray?
        
        @JvmStatic
        external fun nativeDelete(handle: Long, key: ByteArray): Int
        
        @JvmStatic
        external fun nativeGetRootHash(handle: Long): ByteArray
    }
    
    constructor(dataDir: String) : this(nativeInit(dataDir)) {
        if (handle == 0L) {
            throw AmDbException("Failed to initialize database")
        }
    }
    
    fun close() {
        nativeClose(handle)
    }
    
    fun put(key: ByteArray, value: ByteArray): ByteArray {
        return nativePut(handle, key, value)
    }
    
    fun get(key: ByteArray, version: Int = 0): ByteArray? {
        return nativeGet(handle, key, version)
    }
    
    fun delete(key: ByteArray) {
        val status = nativeDelete(handle, key)
        if (status != 0) {
            throw AmDbException("Delete failed")
        }
    }
    
    fun getRootHash(): ByteArray {
        return nativeGetRootHash(handle)
    }
}

class AmDbException(message: String) : Exception(message)

