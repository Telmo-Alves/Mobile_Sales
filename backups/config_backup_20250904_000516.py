# Configuração do Firebird para fdb
FIREBIRD_CONFIG = {
    'host': '192.168.0.201',
    'port': 3055,
    'database': 'gescom_risatel',
    'user': 'SYSDBA',
    'password': 'eampdpg',
    'charset': 'WIN1252'
}

# Configuração dos Armazéns
WAREHOUSE_CONFIG = {
    'arm_ini': 3,    # Armazém inicial
    'arm_fim': 4   # Armazém final
}

# Configuração Flask
SECRET_KEY = 'chave-flask-mobile-sales'
DEBUG = True
