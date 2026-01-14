/**
 * AmDb C API 实现
 * 使用Python C API调用Python实现
 */

#include "amdb.h"
#include <Python.h>
#include <string.h>
#include <stdlib.h>

// Python模块路径
#define PYTHON_MODULE "src.amdb.database"
#define PYTHON_CLASS "Database"

// 全局Python模块
static PyObject* g_amdb_module = NULL;
static PyObject* g_database_class = NULL;

// 初始化Python环境
static int init_python() {
    if (Py_IsInitialized()) {
        return 0;
    }
    
    Py_Initialize();
    if (!Py_IsInitialized()) {
        return -1;
    }
    
    // 导入模块
    g_amdb_module = PyImport_ImportModule(PYTHON_MODULE);
    if (!g_amdb_module) {
        PyErr_Print();
        return -1;
    }
    
    // 获取Database类
    g_database_class = PyObject_GetAttrString(g_amdb_module, PYTHON_CLASS);
    if (!g_database_class) {
        PyErr_Print();
        return -1;
    }
    
    return 0;
}

// 清理Python环境
static void cleanup_python() {
    if (g_database_class) {
        Py_DECREF(g_database_class);
        g_database_class = NULL;
    }
    if (g_amdb_module) {
        Py_DECREF(g_amdb_module);
        g_amdb_module = NULL;
    }
    if (Py_IsInitialized()) {
        Py_Finalize();
    }
}

// 创建Python Database实例
static PyObject* create_database_instance(const char* data_dir) {
    PyObject* args = PyTuple_New(1);
    PyObject* data_dir_str = PyUnicode_FromString(data_dir);
    PyTuple_SetItem(args, 0, data_dir_str);
    
    PyObject* instance = PyObject_CallObject(g_database_class, args);
    Py_DECREF(args);
    
    return instance;
}

// 转换Python异常到状态码
static amdb_status_t handle_python_error() {
    if (PyErr_Occurred()) {
        PyErr_Print();
        return AMDB_ERROR;
    }
    return AMDB_OK;
}

amdb_status_t amdb_init(const char* data_dir, amdb_handle_t* handle) {
    if (init_python() != 0) {
        return AMDB_ERROR;
    }
    
    PyObject* db = create_database_instance(data_dir);
    if (!db) {
        return handle_python_error();
    }
    
    *handle = (amdb_handle_t)db;
    return AMDB_OK;
}

amdb_status_t amdb_close(amdb_handle_t handle) {
    if (!handle) {
        return AMDB_INVALID_ARG;
    }
    
    PyObject* db = (PyObject*)handle;
    
    // 调用flush方法
    PyObject* result = PyObject_CallMethod(db, "flush", NULL);
    if (result) {
        Py_DECREF(result);
    }
    
    Py_DECREF(db);
    return AMDB_OK;
}

amdb_status_t amdb_put(amdb_handle_t handle,
                       const uint8_t* key, size_t key_len,
                       const uint8_t* value, size_t value_len,
                       uint8_t* root_hash) {
    if (!handle || !key || !value) {
        return AMDB_INVALID_ARG;
    }
    
    PyObject* db = (PyObject*)handle;
    
    // 创建Python字节对象
    PyObject* key_obj = PyBytes_FromStringAndSize((const char*)key, key_len);
    PyObject* value_obj = PyBytes_FromStringAndSize((const char*)value, value_len);
    
    // 调用put方法
    PyObject* args = PyTuple_New(2);
    PyTuple_SetItem(args, 0, key_obj);
    PyTuple_SetItem(args, 1, value_obj);
    
    PyObject* result = PyObject_CallMethod(db, "put", "OO", key_obj, value_obj);
    Py_DECREF(args);
    
    if (!result) {
        return handle_python_error();
    }
    
    // 提取结果
    if (PyTuple_Check(result) && PyTuple_Size(result) == 2) {
        PyObject* success = PyTuple_GetItem(result, 0);
        PyObject* root_hash_obj = PyTuple_GetItem(result, 1);
        
        if (PyObject_IsTrue(success) && PyBytes_Check(root_hash_obj)) {
            const char* hash_data = PyBytes_AsString(root_hash_obj);
            size_t hash_len = PyBytes_Size(root_hash_obj);
            if (hash_len >= 32) {
                memcpy(root_hash, hash_data, 32);
            }
        }
    }
    
    Py_DECREF(result);
    return AMDB_OK;
}

amdb_status_t amdb_get(amdb_handle_t handle,
                       const uint8_t* key, size_t key_len,
                       uint32_t version,
                       amdb_result_t* result) {
    if (!handle || !key || !result) {
        return AMDB_INVALID_ARG;
    }
    
    PyObject* db = (PyObject*)handle;
    PyObject* key_obj = PyBytes_FromStringAndSize((const char*)key, key_len);
    
    PyObject* value_obj = NULL;
    if (version == 0) {
        value_obj = PyObject_CallMethod(db, "get", "O", key_obj);
    } else {
        PyObject* version_obj = PyLong_FromUnsignedLong(version);
        value_obj = PyObject_CallMethod(db, "get", "OO", key_obj, version_obj);
        Py_DECREF(version_obj);
    }
    
    Py_DECREF(key_obj);
    
    if (!value_obj) {
        result->status = handle_python_error();
        result->data = NULL;
        result->data_len = 0;
        return result->status;
    }
    
    if (value_obj == Py_None) {
        result->status = AMDB_NOT_FOUND;
        result->data = NULL;
        result->data_len = 0;
        Py_DECREF(value_obj);
        return AMDB_NOT_FOUND;
    }
    
    if (PyBytes_Check(value_obj)) {
        const char* data = PyBytes_AsString(value_obj);
        size_t data_len = PyBytes_Size(value_obj);
        
        result->data = malloc(data_len);
        if (!result->data) {
            Py_DECREF(value_obj);
            return AMDB_MEMORY_ERROR;
        }
        
        memcpy(result->data, data, data_len);
        result->data_len = data_len;
        result->status = AMDB_OK;
    } else {
        result->status = AMDB_ERROR;
        result->data = NULL;
        result->data_len = 0;
    }
    
    Py_DECREF(value_obj);
    return result->status;
}

amdb_status_t amdb_delete(amdb_handle_t handle,
                          const uint8_t* key, size_t key_len) {
    // 简化实现：通过put空值实现删除
    uint8_t empty_value = 0;
    uint8_t root_hash[32];
    return amdb_put(handle, key, key_len, &empty_value, 0, root_hash);
}

amdb_status_t amdb_batch_put(amdb_handle_t handle,
                             const uint8_t** keys, const size_t* key_lens,
                             const uint8_t** values, const size_t* value_lens,
                             size_t count,
                             uint8_t* root_hash) {
    if (!handle || !keys || !values || count == 0) {
        return AMDB_INVALID_ARG;
    }
    
    PyObject* db = (PyObject*)handle;
    
    // 创建Python列表
    PyObject* items = PyList_New(count);
    for (size_t i = 0; i < count; i++) {
        PyObject* key_obj = PyBytes_FromStringAndSize((const char*)keys[i], key_lens[i]);
        PyObject* value_obj = PyBytes_FromStringAndSize((const char*)values[i], value_lens[i]);
        PyObject* item = PyTuple_New(2);
        PyTuple_SetItem(item, 0, key_obj);
        PyTuple_SetItem(item, 1, value_obj);
        PyList_SetItem(items, i, item);
    }
    
    PyObject* result = PyObject_CallMethod(db, "batch_put", "O", items);
    Py_DECREF(items);
    
    if (!result) {
        return handle_python_error();
    }
    
    if (PyTuple_Check(result) && PyTuple_Size(result) == 2) {
        PyObject* root_hash_obj = PyTuple_GetItem(result, 1);
        if (PyBytes_Check(root_hash_obj)) {
            const char* hash_data = PyBytes_AsString(root_hash_obj);
            memcpy(root_hash, hash_data, 32);
        }
    }
    
    Py_DECREF(result);
    return AMDB_OK;
}

amdb_status_t amdb_get_root_hash(amdb_handle_t handle, uint8_t* root_hash) {
    if (!handle || !root_hash) {
        return AMDB_INVALID_ARG;
    }
    
    PyObject* db = (PyObject*)handle;
    PyObject* result = PyObject_CallMethod(db, "get_root_hash", NULL);
    
    if (!result) {
        return handle_python_error();
    }
    
    if (PyBytes_Check(result)) {
        const char* hash_data = PyBytes_AsString(result);
        memcpy(root_hash, hash_data, 32);
        Py_DECREF(result);
        return AMDB_OK;
    }
    
    Py_DECREF(result);
    return AMDB_ERROR;
}

void amdb_free_result(amdb_result_t* result) {
    if (result && result->data) {
        free(result->data);
        result->data = NULL;
        result->data_len = 0;
    }
    if (result && result->error_msg) {
        free(result->error_msg);
        result->error_msg = NULL;
    }
}

const char* amdb_error_string(amdb_status_t status) {
    switch (status) {
        case AMDB_OK: return "Success";
        case AMDB_ERROR: return "General error";
        case AMDB_NOT_FOUND: return "Not found";
        case AMDB_INVALID_ARG: return "Invalid argument";
        case AMDB_IO_ERROR: return "I/O error";
        case AMDB_MEMORY_ERROR: return "Memory error";
        default: return "Unknown error";
    }
}

// 其他函数的简化实现
amdb_status_t amdb_range_query(amdb_handle_t handle,
                               const uint8_t* start_key, size_t start_key_len,
                               const uint8_t* end_key, size_t end_key_len,
                               amdb_result_t** results, size_t* result_count) {
    // TODO: 完整实现
    *results = NULL;
    *result_count = 0;
    return AMDB_OK;
}

amdb_status_t amdb_get_history(amdb_handle_t handle,
                              const uint8_t* key, size_t key_len,
                              uint32_t start_version, uint32_t end_version,
                              uint32_t** versions, size_t* version_count) {
    // TODO: 完整实现
    *versions = NULL;
    *version_count = 0;
    return AMDB_OK;
}

amdb_status_t amdb_verify(amdb_handle_t handle,
                         const uint8_t* key, size_t key_len,
                         const uint8_t* value, size_t value_len,
                         const uint8_t** proof, size_t proof_count,
                         bool* valid) {
    // TODO: 完整实现
    *valid = false;
    return AMDB_OK;
}

amdb_status_t amdb_begin_transaction(amdb_handle_t handle, amdb_tx_handle_t* tx_handle) {
    // TODO: 完整实现
    *tx_handle = NULL;
    return AMDB_OK;
}

amdb_status_t amdb_commit_transaction(amdb_handle_t handle, amdb_tx_handle_t tx_handle) {
    // TODO: 完整实现
    return AMDB_OK;
}

amdb_status_t amdb_rollback_transaction(amdb_handle_t handle, amdb_tx_handle_t tx_handle) {
    // TODO: 完整实现
    return AMDB_OK;
}

void amdb_free_results(amdb_result_t* results, size_t count) {
    if (results) {
        for (size_t i = 0; i < count; i++) {
            amdb_free_result(&results[i]);
        }
        free(results);
    }
}

