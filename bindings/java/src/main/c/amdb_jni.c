/**
 * AmDb JNI实现
 */

#include <jni.h>
#include "amdb.h"
#include <string.h>

JNIEXPORT jlong JNICALL
Java_com_amdb_AmDb_nativeInit(JNIEnv *env, jobject obj, jstring dataDir) {
    const char *c_data_dir = (*env)->GetStringUTFChars(env, dataDir, NULL);
    amdb_handle_t handle;
    amdb_status_t status = amdb_init(c_data_dir, &handle);
    (*env)->ReleaseStringUTFChars(env, dataDir, c_data_dir);
    
    if (status != AMDB_OK) {
        return 0;
    }
    return (jlong)handle;
}

JNIEXPORT void JNICALL
Java_com_amdb_AmDb_nativeClose(JNIEnv *env, jobject obj, jlong handle) {
    amdb_close((amdb_handle_t)handle);
}

JNIEXPORT jint JNICALL
Java_com_amdb_AmDb_nativePut(JNIEnv *env, jobject obj, jlong handle,
                             jbyteArray key, jbyteArray value, jbyteArray rootHash) {
    jbyte *key_bytes = (*env)->GetByteArrayElements(env, key, NULL);
    jsize key_len = (*env)->GetArrayLength(env, key);
    jbyte *value_bytes = (*env)->GetByteArrayElements(env, value, NULL);
    jsize value_len = (*env)->GetArrayLength(env, value);
    
    uint8_t root_hash[32];
    amdb_status_t status = amdb_put(
        (amdb_handle_t)handle,
        (uint8_t*)key_bytes, key_len,
        (uint8_t*)value_bytes, value_len,
        root_hash
    );
    
    if (status == AMDB_OK) {
        (*env)->SetByteArrayRegion(env, rootHash, 0, 32, (jbyte*)root_hash);
    }
    
    (*env)->ReleaseByteArrayElements(env, key, key_bytes, JNI_ABORT);
    (*env)->ReleaseByteArrayElements(env, value, value_bytes, JNI_ABORT);
    
    return (jint)status;
}

JNIEXPORT jbyteArray JNICALL
Java_com_amdb_AmDb_nativeGet(JNIEnv *env, jobject obj, jlong handle,
                              jbyteArray key, jint version) {
    jbyte *key_bytes = (*env)->GetByteArrayElements(env, key, NULL);
    jsize key_len = (*env)->GetArrayLength(env, key);
    
    amdb_result_t result;
    amdb_status_t status = amdb_get(
        (amdb_handle_t)handle,
        (uint8_t*)key_bytes, key_len,
        (uint32_t)version,
        &result
    );
    
    (*env)->ReleaseByteArrayElements(env, key, key_bytes, JNI_ABORT);
    
    if (status != AMDB_OK || result.data == NULL) {
        amdb_free_result(&result);
        return NULL;
    }
    
    jbyteArray j_result = (*env)->NewByteArray(env, result.data_len);
    (*env)->SetByteArrayRegion(env, j_result, 0, result.data_len, (jbyte*)result.data);
    
    amdb_free_result(&result);
    return j_result;
}

JNIEXPORT jint JNICALL
Java_com_amdb_AmDb_nativeDelete(JNIEnv *env, jobject obj, jlong handle, jbyteArray key) {
    jbyte *key_bytes = (*env)->GetByteArrayElements(env, key, NULL);
    jsize key_len = (*env)->GetArrayLength(env, key);
    
    amdb_status_t status = amdb_delete((amdb_handle_t)handle, (uint8_t*)key_bytes, key_len);
    
    (*env)->ReleaseByteArrayElements(env, key, key_bytes, JNI_ABORT);
    return (jint)status;
}

JNIEXPORT jint JNICALL
Java_com_amdb_AmDb_nativeGetRootHash(JNIEnv *env, jobject obj, jlong handle, jbyteArray rootHash) {
    uint8_t root_hash[32];
    amdb_status_t status = amdb_get_root_hash((amdb_handle_t)handle, root_hash);
    
    if (status == AMDB_OK) {
        (*env)->SetByteArrayRegion(env, rootHash, 0, 32, (jbyte*)root_hash);
    }
    
    return (jint)status;
}

JNIEXPORT jstring JNICALL
Java_com_amdb_AmDb_getErrorString(JNIEnv *env, jobject obj, jint status) {
    const char *error_str = amdb_error_string((amdb_status_t)status);
    return (*env)->NewStringUTF(env, error_str);
}

