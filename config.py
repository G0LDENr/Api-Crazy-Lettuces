# config.py
import os
import sys
import atexit
import subprocess
import platform
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

# ========== CONFIGURACIÓN DE SPARK ==========
# Configurar la ruta de Python explícitamente para PySpark
if sys.executable:
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# Variable global para la sesión de Spark
_spark_session = None

def kill_pyspark_workers():
    """Mata todos los procesos workers de PySpark que queden colgados"""
    try:
        current_pid = os.getpid()
        system = platform.system()
        
        if system == "Windows":
            # Buscar procesos python con pyspark en Windows
            result = subprocess.run(
                'wmic process where "name like \'%python%\' and CommandLine like \'%pyspark%\'" get ProcessId',
                capture_output=True, text=True, shell=True
            )
            
            lines = result.stdout.strip().split('\n')
            killed = 0
            
            for line in lines:
                line = line.strip()
                if line and line.isdigit():
                    pid = int(line)
                    if pid != current_pid:
                        subprocess.run(f'taskkill /F /PID {pid}', 
                                        shell=True, 
                                        capture_output=True)
                        killed += 1
            
            if killed > 0:
                print(f"Workers eliminados: {killed}")
            
    except Exception as e:
        print(f"Error al limpiar workers: {e}")

def get_spark_session():
    """Obtener o crear una sesión de Spark singleton"""
    global _spark_session
    if _spark_session is None:
        try:
            from pyspark.sql import SparkSession
            
            print("Creando SparkSession...")
            _spark_session = SparkSession.builder \
                .appName("AnalisisSuplementos") \
                .config("spark.driver.host", "localhost") \
                .config("spark.sql.adaptive.enabled", "false") \
                .config("spark.ui.showConsoleProgress", "false") \
                .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
                .config("spark.sql.execution.arrow.pyspark.fallback.enabled", "true") \
                .config("spark.python.worker.timeout", "30") \
                .config("spark.sql.execution.arrow.maxRecordsPerBatch", "100") \
                .config("spark.sql.shuffle.partitions", "2") \
                .config("spark.default.parallelism", "2") \
                .config("spark.python.worker.reuse", "false") \
                .config("spark.cleaner.referenceTracking.cleanCheckpoints", "true") \
                .getOrCreate()
            
            _spark_session.sparkContext.setLogLevel("ERROR")
            print("Spark Session inicializada")
            
            # Registrar limpieza al salir
            atexit.register(close_spark_session)
            atexit.register(kill_pyspark_workers)
            
        except Exception as e:
            print(f"Error al crear SparkSession: {e}")
            _spark_session = None
    
    return _spark_session

def close_spark_session():
    """Cerrar la sesión de Spark correctamente"""
    global _spark_session
    if _spark_session:
        try:
            print("Cerrando SparkSession...")
            
            # Limpiar cache primero
            try:
                _spark_session.catalog.clearCache()
            except:
                pass
            
            # Detener SparkSession
            _spark_session.stop()
            _spark_session = None
            print("SparkSession cerrada correctamente")
            
        except Exception as e:
            print(f"Error al cerrar SparkSession: {e}")
            _spark_session = None

def pyspark_disponible():
    """Verificar si PySpark está disponible"""
    try:
        import pyspark
        return True
    except ImportError:
        return False

def get_pyspark_version():
    """Obtener versión de PySpark si está disponible"""
    try:
        import pyspark
        return pyspark.__version__
    except:
        return None

# Registrar limpieza al final del módulo
atexit.register(kill_pyspark_workers)