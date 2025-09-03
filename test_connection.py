import fdb

# Teste de conexão com fdb
try:
    print("Tentando conectar ao Firebird com fdb...")
    
    conn = fdb.connect(
        host='192.168.0.201',
        port=3055,
        database='gescom_risatel',  # ou path completo: '/path/to/gescom_risatel.fdb'
        user='SYSDBA',
        password='eampdpg',
        charset='WIN1252'
    )
    
    print("✅ Conexão bem sucedida!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT FIRST 1 * FROM RDB$DATABASE")
    result = cursor.fetchone()
    print(f"Teste query: {result}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    print(f"Detalhes: {type(e).__name__}")

# Teste alternativo com DSN string
try:
    print("\nTeste com DSN string...")
    
    dsn = '192.168.0.201/3055:gescom_risatel'
    conn = fdb.connect(
        dsn=dsn,
        user='SYSDBA',
        password='eampdpg',
        charset='WIN1252'
    )
    
    print("✅ Conexão DSN bem sucedida!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT FIRST 1 * FROM RDB$DATABASE")
    result = cursor.fetchone()
    print(f"Teste query: {result}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro DSN: {e}")