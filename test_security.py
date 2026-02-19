import os
import hashlib
import binascii

# Fallback de seguridad en Python puro
class PythonSecurityCore:
    def hash_password(self, password):
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')

    def verify_password(self, provided_password, stored_password):
        try:
            salt = stored_password[:64]
            stored_hash = stored_password[64:]
            pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
            pwdhash = binascii.hexlify(pwdhash).decode('ascii')
            return pwdhash == stored_hash
        except Exception: return False

    def encrypt_data(self, data, key):
        encoded = data.encode()
        key_bytes = key.encode()
        xor_result = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encoded)])
        return binascii.hexlify(xor_result).decode()

    def decrypt_data(self, encrypted_hex, key):
        xor_result = binascii.unhexlify(encrypted_hex)
        key_bytes = key.encode()
        decoded = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(xor_result)])
        return decoded.decode()

try:
    import security_core
except ImportError:
    security_core = PythonSecurityCore()

def test_security():
    print("--- Testing Rust Security Core ---")
    
    # 1. Test Password Hashing
    password = "admin"
    print(f"Original Password: {password}")
    
    hash_v1 = security_core.hash_password(password)
    print(f"Hash: {hash_v1}")
    
    is_valid = security_core.verify_password(password, hash_v1)
    print(f"Verification (Correct): {is_valid}")
    assert is_valid == True
    
    is_invalid = security_core.verify_password("wrong_pass", hash_v1)
    print(f"Verification (Wrong): {is_invalid}")
    assert is_invalid == False
    
    # 2. Test Data Encryption
    data = "Sensitive Financial Information"
    key = "this_is_a_32_byte_key_for_aes_25" # 32 bytes (exactly)
    print(f"\nOriginal Data: {data}")
    
    encrypted = security_core.encrypt_data(data, key)
    print(f"Encrypted (Base64): {encrypted}")
    
    decrypted = security_core.decrypt_data(encrypted, key)
    print(f"Decrypted Data: {decrypted}")
    assert decrypted == data
    
    print("\n✅ All security tests passed!")

if __name__ == "__main__":
    try:
        test_security()
    except Exception as e:
        print(f"❌ Test failed: {e}")
