/**
 * AmDb Swift绑定
 * 使用C interop调用C API
 */

import Foundation

public class AmDb {
    private var handle: OpaquePointer?
    
    public init(dataDir: String) throws {
        var handlePtr: OpaquePointer?
        let status = amdb_init(dataDir, &handlePtr)
        if status != AMDB_OK {
            throw AmDbError.initializationFailed
        }
        self.handle = handlePtr
    }
    
    deinit {
        if let handle = handle {
            amdb_close(handle)
        }
    }
    
    public func put(key: Data, value: Data) throws -> Data {
        var rootHash = Data(count: 32)
        let status = key.withUnsafeBytes { keyBytes in
            value.withUnsafeBytes { valueBytes in
                rootHash.withUnsafeMutableBytes { hashBytes in
                    amdb_put(
                        handle,
                        keyBytes.baseAddress?.assumingMemoryBound(to: UInt8.self),
                        key.count,
                        valueBytes.baseAddress?.assumingMemoryBound(to: UInt8.self),
                        value.count,
                        hashBytes.baseAddress?.assumingMemoryBound(to: UInt8.self)
                    )
                }
            }
        }
        
        if status != AMDB_OK {
            throw AmDbError.operationFailed(status)
        }
        
        return rootHash
    }
    
    public func get(key: Data, version: UInt32 = 0) throws -> Data? {
        var result = AmdbResult()
        let status = key.withUnsafeBytes { keyBytes in
            amdb_get(
                handle,
                keyBytes.baseAddress?.assumingMemoryBound(to: UInt8.self),
                key.count,
                version,
                &result
            )
        }
        
        defer {
            amdb_free_result(&result)
        }
        
        if status == AMDB_NOT_FOUND {
            return nil
        }
        
        if status != AMDB_OK {
            throw AmDbError.operationFailed(status)
        }
        
        if let dataPtr = result.data {
            return Data(bytes: dataPtr, count: result.data_len)
        }
        
        return nil
    }
    
    public func delete(key: Data) throws {
        let status = key.withUnsafeBytes { keyBytes in
            amdb_delete(handle, keyBytes.baseAddress?.assumingMemoryBound(to: UInt8.self), key.count)
        }
        
        if status != AMDB_OK {
            throw AmDbError.operationFailed(status)
        }
    }
    
    public func getRootHash() throws -> Data {
        var rootHash = Data(count: 32)
        let status = rootHash.withUnsafeMutableBytes { hashBytes in
            amdb_get_root_hash(handle, hashBytes.baseAddress?.assumingMemoryBound(to: UInt8.self))
        }
        
        if status != AMDB_OK {
            throw AmDbError.operationFailed(status)
        }
        
        return rootHash
    }
}

public enum AmDbError: Error {
    case initializationFailed
    case operationFailed(Int32)
}

// C函数声明
@_silgen_name("amdb_init")
func amdb_init(_ dataDir: UnsafePointer<CChar>, _ handle: UnsafeMutablePointer<OpaquePointer?>) -> Int32

@_silgen_name("amdb_close")
func amdb_close(_ handle: OpaquePointer?) -> Int32

@_silgen_name("amdb_put")
func amdb_put(_ handle: OpaquePointer?,
              _ key: UnsafePointer<UInt8>?,
              _ keyLen: Int,
              _ value: UnsafePointer<UInt8>?,
              _ valueLen: Int,
              _ rootHash: UnsafeMutablePointer<UInt8>?) -> Int32

@_silgen_name("amdb_get")
func amdb_get(_ handle: OpaquePointer?,
              _ key: UnsafePointer<UInt8>?,
              _ keyLen: Int,
              _ version: UInt32,
              _ result: UnsafeMutablePointer<AmdbResult>?) -> Int32

@_silgen_name("amdb_delete")
func amdb_delete(_ handle: OpaquePointer?,
                 _ key: UnsafePointer<UInt8>?,
                 _ keyLen: Int) -> Int32

@_silgen_name("amdb_get_root_hash")
func amdb_get_root_hash(_ handle: OpaquePointer?,
                       _ rootHash: UnsafeMutablePointer<UInt8>?) -> Int32

@_silgen_name("amdb_free_result")
func amdb_free_result(_ result: UnsafeMutablePointer<AmdbResult>?)

struct AmdbResult {
    var status: Int32
    var error_msg: UnsafeMutablePointer<CChar>?
    var data: UnsafeMutableRawPointer?
    var data_len: Int
}

let AMDB_OK: Int32 = 0
let AMDB_NOT_FOUND: Int32 = -2

