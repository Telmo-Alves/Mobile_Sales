#!/usr/bin/env python3
"""
Script de teste para validar a camada de abstração da base de dados
"""

import sys
import os
sys.path.append('/var/www/html/Mobile_Sales')

from database import (
    DatabaseManager, existencias_repo, pedidos_repo, 
    reservas_repo, clientes_repo, artigos_repo, auth_repo
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test basic database connection"""
    print("=" * 50)
    print("TESTE 1: Conexão à Base de Dados")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        
        with db.get_cursor() as cursor:
            cursor.execute("SELECT FIRST 1 * FROM RDB$DATABASE")
            result = cursor.fetchone()
            print("✓ Conexão bem-sucedida!")
            print(f"  Resultado: {result}")
            return True
            
    except Exception as e:
        print(f"✗ Erro de conexão: {str(e)}")
        return False

def test_auth_repository():
    """Test authentication repository"""
    print("\n" + "=" * 50)
    print("TESTE 2: AuthRepository")
    print("=" * 50)
    
    try:
        # Test with a shorter test string to avoid parameter length error
        user_data = auth_repo.authenticate_user('U01', 'test')
        
        if user_data:
            print("✓ Autenticação bem-sucedida!")
            print(f"  Utilizador: {user_data['utilizador']}")
            print(f"  Vendedor: {user_data['vendedor']}")
            print(f"  Nível: {user_data['nivel_acesso']}")
        else:
            print("ℹ Credenciais não encontradas (esperado se não existir utilizador de teste)")
            
        return True
        
    except Exception as e:
        print(f"✗ Erro na autenticação: {str(e)}")
        return False

def test_existencias_repository():
    """Test existencias repository"""
    print("\n" + "=" * 50)
    print("TESTE 3: ExistenciasRepository")
    print("=" * 50)
    
    try:
        # Test search products (use a partial code that might exist)
        resultados = existencias_repo.search_products('E03')
        print(f"✓ Pesquisa de produtos executada!")
        print(f"  Resultados encontrados: {len(resultados)}")
        
        if resultados:
            print(f"  Primeiro resultado: {resultados[0][:3]}...")  # Show first 3 fields
            
            # Test product details for first result
            codigo = resultados[0][1]  # RCodigo
            detalhes = existencias_repo.get_product_details(codigo)
            print(f"  Detalhes para {codigo}: {len(detalhes)} lotes")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na pesquisa de existências: {str(e)}")
        return False

def test_artigos_repository():
    """Test artigos repository"""
    print("\n" + "=" * 50)
    print("TESTE 4: ArtigosRepository")
    print("=" * 50)
    
    try:
        # Try to get info for a common product code pattern
        test_codes = ['E0301AL1CM00B', 'E03', 'A001']  # Adjust based on your data
        
        for codigo in test_codes:
            info = artigos_repo.get_product_info(codigo)
            if info:
                print(f"✓ Produto {codigo} encontrado!")
                print(f"  Descrição: {info['descricao'][:50]}...")
                print(f"  Preços: {info['p_qt1']}, {info['p_qt2']}")
                break
        else:
            print("ℹ Nenhum produto de teste encontrado (normal se códigos não existirem)")
            
        return True
        
    except Exception as e:
        print(f"✗ Erro na consulta de artigos: {str(e)}")
        return False

def test_pedidos_repository():
    """Test pedidos repository"""
    print("\n" + "=" * 50)
    print("TESTE 5: PedidosRepository")
    print("=" * 50)
    
    try:
        # Test getting orders list (using vendor 1 which should have broad access)
        pedidos = pedidos_repo.get_orders_list(1)
        print(f"✓ Lista de pedidos executada!")
        print(f"  Pedidos encontrados: {len(pedidos)}")
        
        if pedidos:
            print(f"  Primeiro pedido: Nº {pedidos[0][0]}, Estado: {pedidos[0][6]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na consulta de pedidos: {str(e)}")
        return False

def test_clientes_repository():
    """Test clientes repository"""
    print("\n" + "=" * 50)
    print("TESTE 6: ClientesRepository")
    print("=" * 50)
    
    try:
        # Test getting clients for vendor 1
        clientes = clientes_repo.get_clients_for_vendor(1)
        print(f"✓ Lista de clientes executada!")
        print(f"  Clientes encontrados: {len(clientes)}")
        
        if clientes:
            print(f"  Primeiro cliente: {clientes[0][0]} - {clientes[0][1][:30]}...")
            
            # Test getting specific client info
            cliente_codigo = clientes[0][0]
            info = clientes_repo.get_client_info(cliente_codigo)
            if info:
                print(f"  Info específica: {info['nome'][:30]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na consulta de clientes: {str(e)}")
        return False

def test_warehouse_config():
    """Test warehouse configuration integration"""
    print("\n" + "=" * 50)
    print("TESTE 7: Configuração de Armazéns")
    print("=" * 50)
    
    try:
        from database import BaseRepository
        repo = BaseRepository()
        arm_ini, arm_fim = repo.get_warehouse_params()
        
        print(f"✓ Configuração de armazéns carregada!")
        print(f"  Armazém inicial: {arm_ini}")
        print(f"  Armazém final: {arm_fim}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro na configuração de armazéns: {str(e)}")
        return False

def test_context_manager():
    """Test database context manager"""
    print("\n" + "=" * 50)
    print("TESTE 8: Context Manager")
    print("=" * 50)
    
    try:
        from database import db
        
        # Test context manager with a simple query
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Utiliza_Web")
            count = cursor.fetchone()[0]
            print(f"✓ Context manager funcionando!")
            print(f"  Utilizadores na tabela Utiliza_Web: {count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro no context manager: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("VALIDAÇÃO DA CAMADA DE ABSTRAÇÃO DA BASE DE DADOS")
    print("Mobile Sales - RISATEL")
    
    tests = [
        test_connection,
        test_auth_repository,
        test_existencias_repository,
        test_artigos_repository,
        test_pedidos_repository,
        test_clientes_repository,
        test_warehouse_config,
        test_context_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Teste falhou com exceção: {str(e)}")
    
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES")
    print("=" * 50)
    print(f"Testes executados: {total}")
    print(f"Testes bem-sucedidos: {passed}")
    print(f"Testes falhados: {total - passed}")
    
    if passed == total:
        print("🎉 Todos os testes passaram! A abstração está funcional.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique as configurações.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)