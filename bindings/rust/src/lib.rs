/**
 * AmDb Rust绑定
 * 使用FFI调用C API
 */

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_uint, c_void};
use std::ptr;

#[repr(C)]
pub struct AmdbHandle {
    _private: [u8; 0],
}

#[repr(C)]
pub struct AmdbResult {
    status: c_int,
    error_msg: *const c_char,
    data: *mut c_void,
    data_len: usize,
}

#[link(name = "amdb")]
extern "C" {
    fn amdb_init(data_dir: *const c_char, handle: *mut *mut AmdbHandle) -> c_int;
    fn amdb_close(handle: *mut AmdbHandle) -> c_int;
    fn amdb_put(
        handle: *mut AmdbHandle,
        key: *const u8,
        key_len: usize,
        value: *const u8,
        value_len: usize,
        root_hash: *mut u8,
    ) -> c_int;
    fn amdb_get(
        handle: *mut AmdbHandle,
        key: *const u8,
        key_len: usize,
        version: c_uint,
        result: *mut AmdbResult,
    ) -> c_int;
    fn amdb_delete(handle: *mut AmdbHandle, key: *const u8, key_len: usize) -> c_int;
    fn amdb_get_root_hash(handle: *mut AmdbHandle, root_hash: *mut u8) -> c_int;
    fn amdb_free_result(result: *mut AmdbResult);
    fn amdb_error_string(status: c_int) -> *const c_char;
}

pub struct Database {
    handle: *mut AmdbHandle,
}

impl Database {
    pub fn new(data_dir: &str) -> Result<Self, String> {
        let c_data_dir = CString::new(data_dir).map_err(|e| e.to_string())?;
        let mut handle: *mut AmdbHandle = ptr::null_mut();
        
        let status = unsafe { amdb_init(c_data_dir.as_ptr(), &mut handle) };
        if status != 0 {
            let error_msg = unsafe { CStr::from_ptr(amdb_error_string(status)) };
            return Err(error_msg.to_string_lossy().into_owned());
        }
        
        Ok(Database { handle })
    }
    
    pub fn put(&self, key: &[u8], value: &[u8]) -> Result<[u8; 32], String> {
        let mut root_hash = [0u8; 32];
        let status = unsafe {
            amdb_put(
                self.handle,
                key.as_ptr(),
                key.len(),
                value.as_ptr(),
                value.len(),
                root_hash.as_mut_ptr(),
            )
        };
        
        if status != 0 {
            let error_msg = unsafe { CStr::from_ptr(amdb_error_string(status)) };
            return Err(error_msg.to_string_lossy().into_owned());
        }
        
        Ok(root_hash)
    }
    
    pub fn get(&self, key: &[u8], version: Option<u32>) -> Result<Option<Vec<u8>>, String> {
        let version = version.unwrap_or(0);
        let mut result = AmdbResult {
            status: 0,
            error_msg: ptr::null(),
            data: ptr::null_mut(),
            data_len: 0,
        };
        
        let status = unsafe {
            amdb_get(
                self.handle,
                key.as_ptr(),
                key.len(),
                version,
                &mut result,
            )
        };
        
        if status == -2 {
            // AMDB_NOT_FOUND
            return Ok(None);
        }
        
        if status != 0 {
            let error_msg = unsafe { CStr::from_ptr(amdb_error_string(status)) };
            return Err(error_msg.to_string_lossy().into_owned());
        }
        
        if result.data.is_null() || result.data_len == 0 {
            unsafe { amdb_free_result(&mut result) };
            return Ok(None);
        }
        
        let data = unsafe {
            std::slice::from_raw_parts(result.data as *const u8, result.data_len)
        }.to_vec();
        
        unsafe { amdb_free_result(&mut result) };
        Ok(Some(data))
    }
    
    pub fn delete(&self, key: &[u8]) -> Result<(), String> {
        let status = unsafe { amdb_delete(self.handle, key.as_ptr(), key.len()) };
        if status != 0 {
            let error_msg = unsafe { CStr::from_ptr(amdb_error_string(status)) };
            return Err(error_msg.to_string_lossy().into_owned());
        }
        Ok(())
    }
    
    pub fn get_root_hash(&self) -> Result<[u8; 32], String> {
        let mut root_hash = [0u8; 32];
        let status = unsafe { amdb_get_root_hash(self.handle, root_hash.as_mut_ptr()) };
        if status != 0 {
            let error_msg = unsafe { CStr::from_ptr(amdb_error_string(status)) };
            return Err(error_msg.to_string_lossy().into_owned());
        }
        Ok(root_hash)
    }
}

impl Drop for Database {
    fn drop(&mut self) {
        unsafe {
            amdb_close(self.handle);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_database() {
        let db = Database::new("./test_data").unwrap();
        let root_hash = db.put(b"key", b"value").unwrap();
        let value = db.get(b"key", None).unwrap();
        assert_eq!(value, Some(b"value".to_vec()));
    }
}

