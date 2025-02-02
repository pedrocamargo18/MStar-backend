from app import app
from extensions import db
from models import User, Mercadoria, Entrada, Saida

# Criar o contexto da aplicação
with app.app_context():
    # Criar usuários
    user1 = User(name="Pedro", email="pedro@email.com", password="Teste@1234")
    user2 = User(name="Maria", email="maria@email.com", password="Janeiro201@")

    # Criar mercadorias
    mercadoria1 = Mercadoria(nome="Celular", nro_registro="12345", fabricante="Samsung", tipo="Eletrônico",
                             descricao="Smartphone Galaxy")
    mercadoria2 = Mercadoria(nome="Notebook", nro_registro="67890", fabricante="Dell", tipo="Informática",
                             descricao="Notebook Inspiron")
    mercadoria3 = Mercadoria(nome="Computador", nro_registro="20568", fabricante="Lenovo", tipo="Informática",
                             descricao="Computador i5")
    mercadoria4 = Mercadoria(nome="Ipad", nro_registro="63598", fabricante="Apple", tipo="Eletrônico",
                             descricao="Ipad X Apple")
    mercadoria5 = Mercadoria(nome="Teclado", nro_registro="45789", fabricante="HyperX", tipo="Periferico",
                             descricao="modelo hibrido mecanico")
    mercadoria6 = Mercadoria(nome="Mouse", nro_registro="74895", fabricante="RedDragon", tipo="Periferico",
                             descricao="mouse 7 botões")

    entrada1 = Entrada(quantidade=10, local="Estoque A", mercadoria_nome="Celular")
    entrada2 = Entrada(quantidade=5, local="Estoque B", mercadoria_nome="Notebook")


    db.session.add_all([user1, user2, mercadoria1, mercadoria2,mercadoria3, mercadoria4,mercadoria5, mercadoria6, entrada1, entrada2,])

    db.session.commit()

print("Banco de dados populado com sucesso!")
