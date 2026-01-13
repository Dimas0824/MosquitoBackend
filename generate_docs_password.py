"""
Helper script untuk generate bcrypt password hash untuk dokumentasi API
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_password_hash(password: str) -> str:
    """Generate bcrypt hash dari password"""
    return pwd_context.hash(password)


if __name__ == "__main__":
    print("=" * 60)
    print("Generate Password Hash untuk Dokumentasi API")
    print("=" * 60)
    
    password = input("\nMasukkan password baru: ")
    
    if not password:
        print("❌ Password tidak boleh kosong!")
        exit(1)
    
    # Generate hash
    password_hash = generate_password_hash(password)
    
    print("\n" + "=" * 60)
    print("✅ Password Hash berhasil dibuat!")
    print("=" * 60)
    print(f"\nPassword Hash:\n{password_hash}")
    print("\n" + "=" * 60)
    print("Cara menggunakan:")
    print("=" * 60)
    print("\n1. Copy password hash di atas")
    print("2. Buka file .env (atau config.py)")
    print("3. Set variable:")
    print(f'   DOCS_PASSWORD_HASH="{password_hash}"')
    print("\n" + "=" * 60)
