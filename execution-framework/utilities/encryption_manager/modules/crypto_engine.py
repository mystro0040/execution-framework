import os
import shutil
import tempfile
from core.config import ENABLE_SAFE_MODE
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.padding import PKCS7
from secrets import token_bytes

def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())

def encrypt_directory(target_dir, encrypted_file, salt_file, password):
    if not os.path.exists(target_dir):
        return False, "Directory not found."

    # Zip target to system temp folder (away from the target dir)
    temp_zip = tempfile.mktemp(suffix='.zip')
    shutil.make_archive(temp_zip.replace('.zip', ''), 'zip', target_dir)

    salt = token_bytes(16)
    with open(salt_file, "wb") as f:
        f.write(salt)

    key = derive_key(password, salt)

    with open(temp_zip, "rb") as f:
        plaintext_bytes = f.read()

    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plaintext_bytes) + padder.finalize()

    iv = token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    with open(encrypted_file, "wb") as f:
        f.write(iv + ciphertext)

    # Safe Mode Validation
    if ENABLE_SAFE_MODE:
        try:
            with open(encrypted_file, "rb") as f:
                test_iv = f.read(16)
                test_ciphertext = f.read()

            test_cipher = Cipher(algorithms.AES(key), modes.CBC(test_iv), backend=default_backend())
            test_decryptor = test_cipher.decryptor()
            test_padded = test_decryptor.update(test_ciphertext) + test_decryptor.finalize()
            
            test_unpadder = PKCS7(algorithms.AES.block_size).unpadder()
            test_plaintext = test_unpadder.update(test_padded) + test_unpadder.finalize()

            if test_plaintext != plaintext_bytes:
                raise ValueError("Byte mismatch during validation.")
                
        except Exception as e:
            os.remove(temp_zip)
            if os.path.exists(encrypted_file): os.remove(encrypted_file)
            if os.path.exists(salt_file): os.remove(salt_file)
            return False, "Safe Mode Alert: Encryption failed validation. Original files were NOT deleted."

    # Destruction Phase (Keep directory, wipe contents)
    if os.path.exists(temp_zip):
        os.remove(temp_zip)

    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        # Delete everything inside the folder EXCEPT the new vault and salt
        if os.path.abspath(item_path) not in [os.path.abspath(encrypted_file), os.path.abspath(salt_file)]:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

    msg = "Encryption & Validation successful." if ENABLE_SAFE_MODE else "Encryption successful."
    return True, msg


def decrypt_directory(encrypted_file, target_dir, salt_file, password):
    if not os.path.exists(encrypted_file) or not os.path.exists(salt_file):
        return False, "Encrypted vault or salt not found."

    with open(salt_file, "rb") as f:
        salt = f.read()

    key = derive_key(password, salt)

    with open(encrypted_file, "rb") as f:
        iv = f.read(16)
        ciphertext = f.read()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    try:
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(algorithms.AES.block_size).unpadder()
        plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()
    except ValueError:
        return False, "Incorrect password or corrupted data."

    temp_zip = tempfile.mktemp(suffix='.zip')
    with open(temp_zip, "wb") as f:
        f.write(plaintext_bytes)

    # Extract the zip back into the target directory
    shutil.unpack_archive(temp_zip, target_dir, 'zip')

    # Clean up the zip and the vault files
    os.remove(temp_zip)
    os.remove(encrypted_file)
    os.remove(salt_file)

    return True, "Decryption successful."