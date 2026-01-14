/**
 * AmDb C++ API 实现
 */

#include "amdb.hpp"
#include <cstring>
#include <stdexcept>

namespace amdb {

Database::Database(const std::string& data_dir) {
    amdb_status_t status = amdb_init(data_dir.c_str(), &handle_);
    if (status != AMDB_OK) {
        throw std::runtime_error("Failed to initialize database: " + 
                                 std::string(amdb_error_string(status)));
    }
}

Database::~Database() {
    if (handle_) {
        amdb_close(handle_);
    }
}

Database::Database(Database&& other) noexcept : handle_(other.handle_) {
    other.handle_ = nullptr;
}

Database& Database::operator=(Database&& other) noexcept {
    if (this != &other) {
        if (handle_) {
            amdb_close(handle_);
        }
        handle_ = other.handle_;
        other.handle_ = nullptr;
    }
    return *this;
}

bool Database::put(const std::string& key, const std::string& value) {
    return put(std::vector<uint8_t>(key.begin(), key.end()),
               std::vector<uint8_t>(value.begin(), value.end()));
}

bool Database::put(const std::vector<uint8_t>& key, const std::vector<uint8_t>& value) {
    uint8_t root_hash[32];
    amdb_status_t status = amdb_put(handle_,
                                    key.data(), key.size(),
                                    value.data(), value.size(),
                                    root_hash);
    return status == AMDB_OK;
}

std::vector<uint8_t> Database::get(const std::string& key, uint32_t version) {
    return get(std::vector<uint8_t>(key.begin(), key.end()), version);
}

std::vector<uint8_t> Database::get(const std::vector<uint8_t>& key, uint32_t version) {
    amdb_result_t result;
    amdb_status_t status = amdb_get(handle_, key.data(), key.size(), version, &result);
    
    if (status != AMDB_OK) {
        amdb_free_result(&result);
        return {};
    }
    
    std::vector<uint8_t> value(result.data, result.data + result.data_len);
    amdb_free_result(&result);
    return value;
}

bool Database::remove(const std::string& key) {
    return remove(std::vector<uint8_t>(key.begin(), key.end()));
}

bool Database::remove(const std::vector<uint8_t>& key) {
    amdb_status_t status = amdb_delete(handle_, key.data(), key.size());
    return status == AMDB_OK;
}

bool Database::batch_put(const std::vector<std::pair<std::string, std::string>>& items) {
    std::vector<const uint8_t*> keys;
    std::vector<size_t> key_lens;
    std::vector<const uint8_t*> values;
    std::vector<size_t> value_lens;
    
    std::vector<std::vector<uint8_t>> key_storage;
    std::vector<std::vector<uint8_t>> value_storage;
    
    for (const auto& item : items) {
        key_storage.emplace_back(item.first.begin(), item.first.end());
        value_storage.emplace_back(item.second.begin(), item.second.end());
        
        keys.push_back(key_storage.back().data());
        key_lens.push_back(key_storage.back().size());
        values.push_back(value_storage.back().data());
        value_lens.push_back(value_storage.back().size());
    }
    
    uint8_t root_hash[32];
    amdb_status_t status = amdb_batch_put(handle_,
                                         keys.data(), key_lens.data(),
                                         values.data(), value_lens.data(),
                                         items.size(),
                                         root_hash);
    return status == AMDB_OK;
}

std::vector<uint8_t> Database::get_root_hash() {
    uint8_t root_hash[32];
    amdb_status_t status = amdb_get_root_hash(handle_, root_hash);
    
    if (status == AMDB_OK) {
        return std::vector<uint8_t>(root_hash, root_hash + 32);
    }
    return {};
}

Database::Transaction Database::begin_transaction() {
    amdb_tx_handle_t tx_handle;
    amdb_begin_transaction(handle_, &tx_handle);
    return Transaction(tx_handle);
}

// Transaction实现
bool Database::Transaction::put(const std::string& key, const std::string& value) {
    // TODO: 实现事务写入
    return false;
}

bool Database::Transaction::commit() {
    // TODO: 实现提交
    return false;
}

bool Database::Transaction::rollback() {
    // TODO: 实现回滚
    return false;
}

// 辅助函数
std::string to_hex(const std::vector<uint8_t>& data) {
    const char hex_chars[] = "0123456789abcdef";
    std::string result;
    result.reserve(data.size() * 2);
    for (uint8_t byte : data) {
        result += hex_chars[(byte >> 4) & 0xF];
        result += hex_chars[byte & 0xF];
    }
    return result;
}

std::vector<uint8_t> from_hex(const std::string& hex) {
    std::vector<uint8_t> result;
    result.reserve(hex.length() / 2);
    for (size_t i = 0; i < hex.length(); i += 2) {
        uint8_t byte = 0;
        if (i + 1 < hex.length()) {
            byte = (hex[i] >= '0' && hex[i] <= '9' ? hex[i] - '0' : hex[i] - 'a' + 10) << 4;
            byte |= (hex[i+1] >= '0' && hex[i+1] <= '9' ? hex[i+1] - '0' : hex[i+1] - 'a' + 10);
        }
        result.push_back(byte);
    }
    return result;
}

} // namespace amdb

