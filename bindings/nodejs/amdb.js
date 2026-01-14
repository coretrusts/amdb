/**
 * AmDb Node.js绑定
 * 使用node-ffi或node-addon-api
 */

const ffi = require('ffi-napi');
const ref = require('ref-napi');
const Struct = require('ref-struct-di')(ref);

// 定义C类型
const uint8_t = ref.types.uint8;
const uint32_t = ref.types.uint32;
const size_t = ref.types.size_t;
const voidPtr = ref.refType(ref.types.void);

// 定义结构体
const AmdbResult = Struct({
    status: 'int',
    error_msg: 'string',
    data: voidPtr,
    data_len: size_t
});

// 加载C库
const amdb = ffi.Library('./libamdb', {
    'amdb_init': ['int', ['string', 'pointer']],
    'amdb_close': ['int', ['pointer']],
    'amdb_put': ['int', ['pointer', 'pointer', size_t, 'pointer', size_t, 'pointer']],
    'amdb_get': ['int', ['pointer', 'pointer', size_t, uint32_t, 'pointer']],
    'amdb_delete': ['int', ['pointer', 'pointer', size_t]],
    'amdb_batch_put': ['int', ['pointer', 'pointer', 'pointer', 'pointer', 'pointer', size_t, 'pointer']],
    'amdb_get_root_hash': ['int', ['pointer', 'pointer']],
    'amdb_free_result': ['void', ['pointer']],
    'amdb_error_string': ['string', ['int']]
});

class Database {
    constructor(dataDir) {
        this.handle = ref.alloc('pointer');
        const status = amdb.amdb_init(dataDir, this.handle);
        if (status !== 0) {
            throw new Error(`Failed to initialize database: ${amdb.amdb_error_string(status)}`);
        }
    }

    close() {
        const status = amdb.amdb_close(this.handle.deref());
        if (status !== 0) {
            throw new Error(`Failed to close database: ${amdb.amdb_error_string(status)}`);
        }
    }

    put(key, value) {
        const keyBuf = Buffer.from(key);
        const valueBuf = Buffer.from(value);
        const rootHash = Buffer.alloc(32);
        
        const status = amdb.amdb_put(
            this.handle.deref(),
            keyBuf,
            keyBuf.length,
            valueBuf,
            valueBuf.length,
            rootHash
        );
        
        if (status !== 0) {
            throw new Error(`Put failed: ${amdb.amdb_error_string(status)}`);
        }
        
        return rootHash;
    }

    get(key, version = 0) {
        const keyBuf = Buffer.from(key);
        const result = new AmdbResult();
        
        const status = amdb.amdb_get(
            this.handle.deref(),
            keyBuf,
            keyBuf.length,
            version,
            result.ref()
        );
        
        if (status !== 0) {
            if (status === -2) { // AMDB_NOT_FOUND
                return null;
            }
            throw new Error(`Get failed: ${amdb.amdb_error_string(status)}`);
        }
        
        if (result.data_len > 0) {
            const data = ref.readPointer(result.data, 0, result.data_len);
            return Buffer.from(data);
        }
        
        amdb.amdb_free_result(result.ref());
        return null;
    }

    delete(key) {
        const keyBuf = Buffer.from(key);
        const status = amdb.amdb_delete(this.handle.deref(), keyBuf, keyBuf.length);
        if (status !== 0) {
            throw new Error(`Delete failed: ${amdb.amdb_error_string(status)}`);
        }
    }

    batchPut(items) {
        const count = items.length;
        const keys = items.map(item => Buffer.from(item.key));
        const values = items.map(item => Buffer.from(item.value));
        
        // 创建指针数组
        const keyPtrs = keys.map(k => k);
        const valuePtrs = values.map(v => v);
        const keyLens = keys.map(k => k.length);
        const valueLens = values.map(v => v.length);
        
        const rootHash = Buffer.alloc(32);
        const status = amdb.amdb_batch_put(
            this.handle.deref(),
            keyPtrs,
            keyLens,
            valuePtrs,
            valueLens,
            count,
            rootHash
        );
        
        if (status !== 0) {
            throw new Error(`Batch put failed: ${amdb.amdb_error_string(status)}`);
        }
        
        return rootHash;
    }

    getRootHash() {
        const rootHash = Buffer.alloc(32);
        const status = amdb.amdb_get_root_hash(this.handle.deref(), rootHash);
        if (status !== 0) {
            throw new Error(`Get root hash failed: ${amdb.amdb_error_string(status)}`);
        }
        return rootHash;
    }
}

module.exports = { Database };

