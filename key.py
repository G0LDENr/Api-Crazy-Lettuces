# generar_clave.py
from cryptography.fernet import Fernet

# Generar una clave nueva
key = Fernet.generate_key()

print("\n" + "="*50)
print("AGREGA ESTA LÍNEA A TU ARCHIVO .env:")
print(f"FERNET_KEY={key.decode()}")
print("="*50 + "\n")