from cryptography.fernet import Fernet
import os

key = open(f"{os.path.dirname(__file__)}/key.key", "r").read().encode('utf-8')


def generate_key():
    """
    Function to generate a random key
    Returns:
        bytes: Random key
    """
    return Fernet.generate_key()


def encrypt_password(password):
    """
    Function to encrypt a password.
    Args:
        password (str): The password to encrypt.
    Returns:
        str: Encrypted password.
    """
    password_bytes = password.encode('utf-8')
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password_bytes)

    return encrypted_password.decode('utf-8')


def decrypt_password(password):
    """
    Function to decrypt a password.
    Args:
        password (str): The password to decrypt.
    Returns:
        str: Password.
    """
    fernet = Fernet(key)
    decrypted_password_bytes = fernet.decrypt(password.encode('utf-8'))
    decrypted_password = decrypted_password_bytes.decode('utf-8')

    return decrypted_password
