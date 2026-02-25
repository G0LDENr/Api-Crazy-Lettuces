# config.py
import os
import pymysql
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_pymongo import PyMongo
from dotenv import load_dotenv

load_dotenv()

# Configuración para SQLAlchemy (MySQL)
pymysql.install_as_MySQLdb()
db_sql = SQLAlchemy()
migrate = Migrate()

# Configuración para MongoDB
db_mongo = PyMongo()

# Variable global para el tipo de base de datos
DB_TYPE = os.getenv('DB_TYPE', 'mysql')  # 'mysql' o 'mongodb'

def set_db_type(db_type):
    """Función para cambiar el tipo de base de datos en tiempo de ejecución"""
    global DB_TYPE
    if db_type in ['mysql', 'mongodb']:
        DB_TYPE = db_type
        os.environ['DB_TYPE'] = db_type
        print(f"📌 Base de datos cambiada a: {db_type}")
        return True
    return False

# Configuración para el patrón repositorio
class DatabaseFactory:
    """Factory para crear la conexión de base de datos apropiada"""
    
    @staticmethod
    def get_db():
        return db_sql if DB_TYPE == 'mysql' else db_mongo
    
    @staticmethod
    def get_db_type():
        return DB_TYPE

# Para compatibilidad con código existente
db = db_sql if DB_TYPE == 'mysql' else db_mongo

# Roles (igual para ambas DBs)
ROLES = {
    1: 'admin',
    2: 'client',
}