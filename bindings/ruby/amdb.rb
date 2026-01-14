# AmDb Ruby绑定
# 使用FFI调用C API

require 'ffi'

module AmDb
  extend FFI::Library
  
  # 加载C库
  ffi_lib './libamdb.so'
  
  # 定义C结构
  class AmdbResult < FFI::Struct
    layout :status, :int,
           :error_msg, :pointer,
           :data, :pointer,
           :data_len, :size_t
  end
  
  # 定义C函数
  attach_function :amdb_init, [:string, :pointer], :int
  attach_function :amdb_close, [:pointer], :int
  attach_function :amdb_put, [:pointer, :pointer, :size_t, :pointer, :size_t, :pointer], :int
  attach_function :amdb_get, [:pointer, :pointer, :size_t, :uint32, :pointer], :int
  attach_function :amdb_delete, [:pointer, :pointer, :size_t], :int
  attach_function :amdb_get_root_hash, [:pointer, :pointer], :int
  attach_function :amdb_free_result, [:pointer], :void
  attach_function :amdb_error_string, [:int], :string
  
  class Database
    def initialize(data_dir)
      @handle = FFI::MemoryPointer.new(:pointer)
      status = AmDb.amdb_init(data_dir, @handle)
      if status != 0
        raise "Failed to initialize database: #{AmDb.amdb_error_string(status)}"
      end
      @handle_value = @handle.read_pointer
    end
    
    def close
      if @handle_value
        AmDb.amdb_close(@handle_value)
        @handle_value = nil
      end
    end
    
    def put(key, value)
      key_bytes = key.is_a?(String) ? key.bytes : key
      value_bytes = value.is_a?(String) ? value.bytes : value
      
      root_hash = FFI::MemoryPointer.new(:uint8, 32)
      
      key_ptr = FFI::MemoryPointer.new(:uint8, key_bytes.length)
      key_ptr.write_bytes(key_bytes.pack('C*'))
      
      value_ptr = FFI::MemoryPointer.new(:uint8, value_bytes.length)
      value_ptr.write_bytes(value_bytes.pack('C*'))
      
      status = AmDb.amdb_put(
        @handle_value,
        key_ptr,
        key_bytes.length,
        value_ptr,
        value_bytes.length,
        root_hash
      )
      
      if status != 0
        raise "Put failed: #{AmDb.amdb_error_string(status)}"
      end
      
      root_hash.read_array_of_uint8(32)
    end
    
    def get(key, version = 0)
      key_bytes = key.is_a?(String) ? key.bytes : key
      key_ptr = FFI::MemoryPointer.new(:uint8, key_bytes.length)
      key_ptr.write_bytes(key_bytes.pack('C*'))
      
      result = AmdbResult.new
      status = AmDb.amdb_get(@handle_value, key_ptr, key_bytes.length, version, result)
      
      begin
        if status == -2  # AMDB_NOT_FOUND
          return nil
        end
        
        if status != 0
          raise "Get failed: #{AmDb.amdb_error_string(status)}"
        end
        
        if result[:data_len] > 0
          data_ptr = result[:data]
          data = data_ptr.read_bytes(result[:data_len])
          return data
        end
        
        nil
      ensure
        AmDb.amdb_free_result(result)
      end
    end
    
    def delete(key)
      key_bytes = key.is_a?(String) ? key.bytes : key
      key_ptr = FFI::MemoryPointer.new(:uint8, key_bytes.length)
      key_ptr.write_bytes(key_bytes.pack('C*'))
      
      status = AmDb.amdb_delete(@handle_value, key_ptr, key_bytes.length)
      if status != 0
        raise "Delete failed: #{AmDb.amdb_error_string(status)}"
      end
    end
    
    def get_root_hash
      root_hash = FFI::MemoryPointer.new(:uint8, 32)
      status = AmDb.amdb_get_root_hash(@handle_value, root_hash)
      if status != 0
        raise "Get root hash failed: #{AmDb.amdb_error_string(status)}"
      end
      root_hash.read_array_of_uint8(32)
    end
  end
end

