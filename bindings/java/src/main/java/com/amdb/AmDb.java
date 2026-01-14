/**
 * AmDb Java绑定
 * 使用JNI调用C API
 */

package com.amdb;

public class AmDb {
    static {
        System.loadLibrary("amdb_jni");
    }
    
    private long handle;
    
    public AmDb(String dataDir) throws AmDbException {
        this.handle = nativeInit(dataDir);
        if (this.handle == 0) {
            throw new AmDbException("Failed to initialize database");
        }
    }
    
    public void close() throws AmDbException {
        if (this.handle != 0) {
            nativeClose(this.handle);
            this.handle = 0;
        }
    }
    
    public byte[] put(byte[] key, byte[] value) throws AmDbException {
        byte[] rootHash = new byte[32];
        int status = nativePut(this.handle, key, value, rootHash);
        if (status != 0) {
            throw new AmDbException("Put failed: " + getErrorString(status));
        }
        return rootHash;
    }
    
    public byte[] get(byte[] key, int version) throws AmDbException {
        byte[] result = nativeGet(this.handle, key, version);
        if (result == null) {
            throw new AmDbException("Key not found");
        }
        return result;
    }
    
    public void delete(byte[] key) throws AmDbException {
        int status = nativeDelete(this.handle, key);
        if (status != 0) {
            throw new AmDbException("Delete failed: " + getErrorString(status));
        }
    }
    
    public byte[] getRootHash() throws AmDbException {
        byte[] rootHash = new byte[32];
        int status = nativeGetRootHash(this.handle, rootHash);
        if (status != 0) {
            throw new AmDbException("Get root hash failed: " + getErrorString(status));
        }
        return rootHash;
    }
    
    // Native方法声明
    private native long nativeInit(String dataDir);
    private native void nativeClose(long handle);
    private native int nativePut(long handle, byte[] key, byte[] value, byte[] rootHash);
    private native byte[] nativeGet(long handle, byte[] key, int version);
    private native int nativeDelete(long handle, byte[] key);
    private native int nativeGetRootHash(long handle, byte[] rootHash);
    private native String getErrorString(int status);
    
    @Override
    protected void finalize() throws Throwable {
        close();
        super.finalize();
    }
}

