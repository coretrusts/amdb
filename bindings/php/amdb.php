<?php
/**
 * AmDb PHP绑定
 * 使用FFI (PHP 7.4+)
 */

class AmDb {
    private $ffi;
    private $handle;
    
    public function __construct(string $dataDir) {
        // 定义FFI接口
        $this->ffi = FFI::cdef("
            typedef void* amdb_handle_t;
            typedef enum {
                AMDB_OK = 0,
                AMDB_ERROR = -1,
                AMDB_NOT_FOUND = -2,
                AMDB_INVALID_ARG = -3
            } amdb_status_t;
            
            amdb_status_t amdb_init(const char* data_dir, amdb_handle_t* handle);
            amdb_status_t amdb_close(amdb_handle_t handle);
            amdb_status_t amdb_put(amdb_handle_t handle, 
                                   const uint8_t* key, size_t key_len,
                                   const uint8_t* value, size_t value_len,
                                   uint8_t* root_hash);
            amdb_status_t amdb_get(amdb_handle_t handle,
                                   const uint8_t* key, size_t key_len,
                                   uint32_t version,
                                   void** result_data, size_t* result_len);
            amdb_status_t amdb_delete(amdb_handle_t handle,
                                     const uint8_t* key, size_t key_len);
            amdb_status_t amdb_get_root_hash(amdb_handle_t handle, uint8_t* root_hash);
            const char* amdb_error_string(amdb_status_t status);
        ", "./libamdb.so");
        
        $handle = $this->ffi->new("void*");
        $status = $this->ffi->amdb_init($dataDir, FFI::addr($handle));
        if ($status !== 0) {
            throw new Exception("Failed to initialize database: " . 
                              $this->ffi->amdb_error_string($status));
        }
        $this->handle = $handle;
    }
    
    public function __destruct() {
        if ($this->handle) {
            $this->ffi->amdb_close($this->handle);
        }
    }
    
    public function put(string $key, string $value): string {
        $keyBytes = $this->stringToBytes($key);
        $valueBytes = $this->stringToBytes($value);
        $rootHash = $this->ffi->new("uint8_t[32]");
        
        $status = $this->ffi->amdb_put(
            $this->handle,
            $keyBytes,
            strlen($key),
            $valueBytes,
            strlen($value),
            $rootHash
        );
        
        if ($status !== 0) {
            throw new Exception("Put failed: " . $this->ffi->amdb_error_string($status));
        }
        
        return $this->bytesToString($rootHash, 32);
    }
    
    public function get(string $key, int $version = 0): ?string {
        $keyBytes = $this->stringToBytes($key);
        $resultData = $this->ffi->new("void*");
        $resultLen = $this->ffi->new("size_t");
        
        $status = $this->ffi->amdb_get(
            $this->handle,
            $keyBytes,
            strlen($key),
            $version,
            FFI::addr($resultData),
            FFI::addr($resultLen)
        );
        
        if ($status !== 0) {
            if ($status === -2) { // AMDB_NOT_FOUND
                return null;
            }
            throw new Exception("Get failed: " . $this->ffi->amdb_error_string($status));
        }
        
        if ($resultLen->cdata > 0) {
            $data = FFI::string($resultData->cdata, $resultLen->cdata);
            return $data;
        }
        
        return null;
    }
    
    public function delete(string $key): void {
        $keyBytes = $this->stringToBytes($key);
        $status = $this->ffi->amdb_delete($this->handle, $keyBytes, strlen($key));
        if ($status !== 0) {
            throw new Exception("Delete failed: " . $this->ffi->amdb_error_string($status));
        }
    }
    
    public function getRootHash(): string {
        $rootHash = $this->ffi->new("uint8_t[32]");
        $status = $this->ffi->amdb_get_root_hash($this->handle, $rootHash);
        if ($status !== 0) {
            throw new Exception("Get root hash failed: " . 
                              $this->ffi->amdb_error_string($status));
        }
        return $this->bytesToString($rootHash, 32);
    }
    
    private function stringToBytes(string $str): \FFI\CData {
        $len = strlen($str);
        $bytes = $this->ffi->new("uint8_t[$len]");
        for ($i = 0; $i < $len; $i++) {
            $bytes[$i] = ord($str[$i]);
        }
        return $bytes;
    }
    
    private function bytesToString(\FFI\CData $bytes, int $len): string {
        $str = '';
        for ($i = 0; $i < $len; $i++) {
            $str .= chr($bytes[$i]);
        }
        return $str;
    }
}

