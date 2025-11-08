print("=== ТЕСТ БИБЛИОТЕК ===")

try:
    from flask import Flask
    print("✅ Flask - ОК")
except ImportError as e:
    print(f"❌ Flask: {e}")

try:
    from werkzeug.security import generate_password_hash
    hash_test = generate_password_hash("test")
    print("✅ Werkzeug - ОК")
except ImportError as e:
    print(f"❌ Werkzeug: {e}")

try:
    import pymysql
    print("✅ PyMySQL - ОК") 
except ImportError as e:
    print(f"❌ PyMySQL: {e}")

print("=== ТЕСТ ЗАВЕРШЕН ===")