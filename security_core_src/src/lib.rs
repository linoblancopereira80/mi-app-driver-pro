use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use argon2::{
    password_hash::{rand_core::OsRng, PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};
use aes_gcm::{
    aead::{Aead, KeyInit, Payload},
    Aes256Gcm, Nonce,
};
use base64::{engine::general_purpose, Engine as _};
use rand::RngCore;

#[pyfunction]
fn hash_password(password: String) -> PyResult<String> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    let password_hash = argon2
        .hash_password(password.as_bytes(), &salt)
        .map_err(|e| PyValueError::new_err(format!("Hashing error: {}", e)))?
        .to_string();
    Ok(password_hash)
}

#[pyfunction]
fn verify_password(password: String, hash: String) -> PyResult<bool> {
    let parsed_hash = PasswordHash::new(&hash)
        .map_err(|e| PyValueError::new_err(format!("Invalid hash: {}", e)))?;
    let argon2 = Argon2::default();
    Ok(argon2.verify_password(password.as_bytes(), &parsed_hash).is_ok())
}

#[pyfunction]
fn encrypt_data(data: String, key_str: String) -> PyResult<String> {
    let key_bytes = key_str.as_bytes();
    if key_bytes.len() != 32 {
        return Err(PyValueError::new_err("Key must be 32 bytes for AES-256"));
    }
    
    let key = aes_gcm::Key::<Aes256Gcm>::from_slice(key_bytes);
    let cipher = Aes256Gcm::new(key);
    
    let mut nonce_bytes = [0u8; 12];
    rand::thread_rng().fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    
    let ciphertext = cipher
        .encrypt(nonce, data.as_bytes())
        .map_err(|e| PyValueError::new_err(format!("Encryption error: {}", e)))?;
        
    let mut combined = nonce_bytes.to_vec();
    combined.extend_from_slice(&ciphertext);
    
    Ok(general_purpose::STANDARD.encode(combined))
}

#[pyfunction]
fn decrypt_data(encrypted_base64: String, key_str: String) -> PyResult<String> {
    let key_bytes = key_str.as_bytes();
    if key_bytes.len() != 32 {
        return Err(PyValueError::new_err("Key must be 32 bytes for AES-256"));
    }
    
    let encrypted_data = general_purpose::STANDARD
        .decode(encrypted_base64)
        .map_err(|e| PyValueError::new_err(format!("Invalid base64: {}", e)))?;
        
    if encrypted_data.len() < 12 {
        return Err(PyValueError::new_err("Encrypted data too short"));
    }
    
    let (nonce_bytes, ciphertext) = encrypted_data.split_at(12);
    let key = aes_gcm::Key::<Aes256Gcm>::from_slice(key_bytes);
    let cipher = Aes256Gcm::new(key);
    let nonce = Nonce::from_slice(nonce_bytes);
    
    let plaintext = cipher
        .decrypt(nonce, ciphertext)
        .map_err(|e| PyValueError::new_err(format!("Decryption error: {}", e)))?;
        
    String::from_utf8(plaintext)
        .map_err(|e| PyValueError::new_err(format!("UTF-8 error: {}", e)))
}

#[pymodule]
fn security_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hash_password, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_data, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_data, m)?)?;
    Ok(())
}
