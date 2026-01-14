/**
 * AmDb Go绑定
 * 使用CGO调用C API
 */

package amdb

/*
#cgo CFLAGS: -I${SRCDIR}/../c
#cgo LDFLAGS: -L${SRCDIR}/../c -lamdb
#include "amdb.h"
#include <stdlib.h>
*/
import "C"
import (
	"errors"
	"unsafe"
)

// Database 数据库句柄
type Database struct {
	handle C.amdb_handle_t
}

// NewDatabase 创建新数据库实例
func NewDatabase(dataDir string) (*Database, error) {
	cDataDir := C.CString(dataDir)
	defer C.free(unsafe.Pointer(cDataDir))

	var handle C.amdb_handle_t
	status := C.amdb_init(cDataDir, &handle)
	if status != C.AMDB_OK {
		return nil, errors.New(C.GoString(C.amdb_error_string(status)))
	}

	return &Database{handle: handle}, nil
}

// Close 关闭数据库
func (db *Database) Close() error {
	status := C.amdb_close(db.handle)
	if status != C.AMDB_OK {
		return errors.New(C.GoString(C.amdb_error_string(status)))
	}
	return nil
}

// Put 写入键值对
func (db *Database) Put(key, value []byte) ([]byte, error) {
	var rootHash [32]C.uint8_t
	status := C.amdb_put(
		db.handle,
		(*C.uint8_t)(unsafe.Pointer(&key[0])), C.size_t(len(key)),
		(*C.uint8_t)(unsafe.Pointer(&value[0])), C.size_t(len(value)),
		&rootHash[0],
	)
	if status != C.AMDB_OK {
		return nil, errors.New(C.GoString(C.amdb_error_string(status)))
	}
	return C.GoBytes(unsafe.Pointer(&rootHash[0]), 32), nil
}

// Get 读取键值对
func (db *Database) Get(key []byte, version uint32) ([]byte, error) {
	var result C.amdb_result_t
	status := C.amdb_get(
		db.handle,
		(*C.uint8_t)(unsafe.Pointer(&key[0])), C.size_t(len(key)),
		C.uint32_t(version),
		&result,
	)
	defer C.amdb_free_result(&result)

	if status != C.AMDB_OK {
		if status == C.AMDB_NOT_FOUND {
			return nil, errors.New("key not found")
		}
		return nil, errors.New(C.GoString(C.amdb_error_string(status)))
	}

	if result.data == nil {
		return nil, errors.New("no data")
	}

	data := C.GoBytes(result.data, C.int(result.data_len))
	return data, nil
}

// Delete 删除键值对
func (db *Database) Delete(key []byte) error {
	status := C.amdb_delete(
		db.handle,
		(*C.uint8_t)(unsafe.Pointer(&key[0])), C.size_t(len(key)),
	)
	if status != C.AMDB_OK {
		return errors.New(C.GoString(C.amdb_error_string(status)))
	}
	return nil
}

// BatchPut 批量写入
func (db *Database) BatchPut(items map[string][]byte) ([]byte, error) {
	keys := make([]*C.uint8_t, len(items))
	keyLens := make([]C.size_t, len(items))
	values := make([]*C.uint8_t, len(items))
	valueLens := make([]C.size_t, len(items))

	// 保存Go数据，防止被GC
	keyData := make([][]byte, 0, len(items))
	valueData := make([][]byte, 0, len(items))

	i := 0
	for k, v := range items {
		keyBytes := []byte(k)
		keyData = append(keyData, keyBytes)
		valueData = append(valueData, v)

		keys[i] = (*C.uint8_t)(unsafe.Pointer(&keyData[i][0]))
		keyLens[i] = C.size_t(len(keyData[i]))
		values[i] = (*C.uint8_t)(unsafe.Pointer(&valueData[i][0]))
		valueLens[i] = C.size_t(len(valueData[i]))
		i++
	}

	var rootHash [32]C.uint8_t
	status := C.amdb_batch_put(
		db.handle,
		&keys[0], &keyLens[0],
		&values[0], &valueLens[0],
		C.size_t(len(items)),
		&rootHash[0],
	)
	if status != C.AMDB_OK {
		return nil, errors.New(C.GoString(C.amdb_error_string(status)))
	}
	return C.GoBytes(unsafe.Pointer(&rootHash[0]), 32), nil
}

// GetRootHash 获取Merkle根哈希
func (db *Database) GetRootHash() ([]byte, error) {
	var rootHash [32]C.uint8_t
	status := C.amdb_get_root_hash(db.handle, &rootHash[0])
	if status != C.AMDB_OK {
		return nil, errors.New(C.GoString(C.amdb_error_string(status)))
	}
	return C.GoBytes(unsafe.Pointer(&rootHash[0]), 32), nil
}
