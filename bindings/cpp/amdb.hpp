/**
 * AmDb C++ API
 * C++封装，提供更友好的接口
 */

#ifndef AMDB_CPP_H
#define AMDB_CPP_H

#include <string>
#include <vector>
#include <memory>
#include <cstdint>
#include "../c/amdb.h"

namespace amdb {

class Database {
public:
    Database(const std::string& data_dir);
    ~Database();
    
    // 禁止拷贝
    Database(const Database&) = delete;
    Database& operator=(const Database&) = delete;
    
    // 移动构造
    Database(Database&& other) noexcept;
    Database& operator=(Database&& other) noexcept;
    
    /**
     * 写入键值对
     */
    bool put(const std::string& key, const std::string& value);
    bool put(const std::vector<uint8_t>& key, const std::vector<uint8_t>& value);
    
    /**
     * 读取键值对
     */
    std::vector<uint8_t> get(const std::string& key, uint32_t version = 0);
    std::vector<uint8_t> get(const std::vector<uint8_t>& key, uint32_t version = 0);
    
    /**
     * 删除键值对
     */
    bool remove(const std::string& key);
    bool remove(const std::vector<uint8_t>& key);
    
    /**
     * 批量写入
     */
    bool batch_put(const std::vector<std::pair<std::string, std::string>>& items);
    
    /**
     * 范围查询
     */
    std::vector<std::pair<std::vector<uint8_t>, std::vector<uint8_t>>> 
    range_query(const std::vector<uint8_t>& start_key, 
                const std::vector<uint8_t>& end_key);
    
    /**
     * 获取版本历史
     */
    std::vector<uint32_t> get_history(const std::string& key, 
                                      uint32_t start_version = 0,
                                      uint32_t end_version = 0);
    
    /**
     * 获取Merkle根哈希
     */
    std::vector<uint8_t> get_root_hash();
    
    /**
     * 验证数据
     */
    bool verify(const std::vector<uint8_t>& key,
                const std::vector<uint8_t>& value,
                const std::vector<std::vector<uint8_t>>& proof);
    
    /**
     * 开始事务
     */
    class Transaction {
    public:
        Transaction(amdb_tx_handle_t handle) : handle_(handle) {}
        ~Transaction() = default;
        
        bool put(const std::string& key, const std::string& value);
        bool commit();
        bool rollback();
        
    private:
        amdb_tx_handle_t handle_;
    };
    
    Transaction begin_transaction();
    
private:
    amdb_handle_t handle_;
};

// 辅助函数
std::string to_hex(const std::vector<uint8_t>& data);
std::vector<uint8_t> from_hex(const std::string& hex);

} // namespace amdb

#endif // AMDB_CPP_H

