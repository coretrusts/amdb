/**
 * AmDb C API
 * 提供C语言接口，作为其他语言绑定的基础
 */

#ifndef AMDB_H
#define AMDB_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// 错误码
typedef enum {
    AMDB_OK = 0,
    AMDB_ERROR = -1,
    AMDB_NOT_FOUND = -2,
    AMDB_INVALID_ARG = -3,
    AMDB_IO_ERROR = -4,
    AMDB_MEMORY_ERROR = -5
} amdb_status_t;

// 数据库句柄
typedef void* amdb_handle_t;

// 事务句柄
typedef void* amdb_tx_handle_t;

// 结果结构
typedef struct {
    amdb_status_t status;
    char* error_msg;
    void* data;
    size_t data_len;
} amdb_result_t;

/**
 * 初始化数据库
 * @param data_dir 数据目录路径
 * @param handle 输出数据库句柄
 * @return 状态码
 */
amdb_status_t amdb_init(const char* data_dir, amdb_handle_t* handle);

/**
 * 关闭数据库
 * @param handle 数据库句柄
 * @return 状态码
 */
amdb_status_t amdb_close(amdb_handle_t handle);

/**
 * 写入键值对
 * @param handle 数据库句柄
 * @param key 键
 * @param key_len 键长度
 * @param value 值
 * @param value_len 值长度
 * @param root_hash 输出Merkle根哈希（32字节）
 * @return 状态码
 */
amdb_status_t amdb_put(amdb_handle_t handle, 
                       const uint8_t* key, size_t key_len,
                       const uint8_t* value, size_t value_len,
                       uint8_t* root_hash);

/**
 * 读取键值对
 * @param handle 数据库句柄
 * @param key 键
 * @param key_len 键长度
 * @param version 版本号（0表示最新版本）
 * @param result 输出结果
 * @return 状态码
 */
amdb_status_t amdb_get(amdb_handle_t handle,
                       const uint8_t* key, size_t key_len,
                       uint32_t version,
                       amdb_result_t* result);

/**
 * 删除键值对
 * @param handle 数据库句柄
 * @param key 键
 * @param key_len 键长度
 * @return 状态码
 */
amdb_status_t amdb_delete(amdb_handle_t handle,
                          const uint8_t* key, size_t key_len);

/**
 * 批量写入
 * @param handle 数据库句柄
 * @param keys 键数组
 * @param key_lens 键长度数组
 * @param values 值数组
 * @param value_lens 值长度数组
 * @param count 数量
 * @param root_hash 输出Merkle根哈希
 * @return 状态码
 */
amdb_status_t amdb_batch_put(amdb_handle_t handle,
                             const uint8_t** keys, const size_t* key_lens,
                             const uint8_t** values, const size_t* value_lens,
                             size_t count,
                             uint8_t* root_hash);

/**
 * 范围查询
 * @param handle 数据库句柄
 * @param start_key 起始键
 * @param start_key_len 起始键长度
 * @param end_key 结束键
 * @param end_key_len 结束键长度
 * @param results 输出结果数组
 * @param result_count 输出结果数量
 * @return 状态码
 */
amdb_status_t amdb_range_query(amdb_handle_t handle,
                               const uint8_t* start_key, size_t start_key_len,
                               const uint8_t* end_key, size_t end_key_len,
                               amdb_result_t** results, size_t* result_count);

/**
 * 获取版本历史
 * @param handle 数据库句柄
 * @param key 键
 * @param key_len 键长度
 * @param start_version 起始版本（0表示从开始）
 * @param end_version 结束版本（0表示到最后）
 * @param versions 输出版本数组
 * @param version_count 输出版本数量
 * @return 状态码
 */
amdb_status_t amdb_get_history(amdb_handle_t handle,
                               const uint8_t* key, size_t key_len,
                               uint32_t start_version, uint32_t end_version,
                               uint32_t** versions, size_t* version_count);

/**
 * 获取Merkle根哈希
 * @param handle 数据库句柄
 * @param root_hash 输出根哈希（32字节）
 * @return 状态码
 */
amdb_status_t amdb_get_root_hash(amdb_handle_t handle, uint8_t* root_hash);

/**
 * 验证数据
 * @param handle 数据库句柄
 * @param key 键
 * @param key_len 键长度
 * @param value 值
 * @param value_len 值长度
 * @param proof 证明数组
 * @param proof_count 证明数量
 * @param valid 输出验证结果
 * @return 状态码
 */
amdb_status_t amdb_verify(amdb_handle_t handle,
                          const uint8_t* key, size_t key_len,
                          const uint8_t* value, size_t value_len,
                          const uint8_t** proof, size_t proof_count,
                          bool* valid);

/**
 * 开始事务
 * @param handle 数据库句柄
 * @param tx_handle 输出事务句柄
 * @return 状态码
 */
amdb_status_t amdb_begin_transaction(amdb_handle_t handle, amdb_tx_handle_t* tx_handle);

/**
 * 提交事务
 * @param handle 数据库句柄
 * @param tx_handle 事务句柄
 * @return 状态码
 */
amdb_status_t amdb_commit_transaction(amdb_handle_t handle, amdb_tx_handle_t tx_handle);

/**
 * 回滚事务
 * @param handle 数据库句柄
 * @param tx_handle 事务句柄
 * @return 状态码
 */
amdb_status_t amdb_rollback_transaction(amdb_handle_t handle, amdb_tx_handle_t tx_handle);

/**
 * 释放结果
 * @param result 结果指针
 */
void amdb_free_result(amdb_result_t* result);

/**
 * 释放结果数组
 * @param results 结果数组
 * @param count 数量
 */
void amdb_free_results(amdb_result_t* results, size_t count);

/**
 * 获取错误信息
 * @param status 状态码
 * @return 错误信息字符串
 */
const char* amdb_error_string(amdb_status_t status);

#ifdef __cplusplus
}
#endif

#endif // AMDB_H

