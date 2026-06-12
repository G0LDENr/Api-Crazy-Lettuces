from flask import Flask, jsonify
from config import db_sql, db_mongo, migrate, DB_TYPE, set_db_type
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
import sys

# IMPORTAR EL SERVICIO DE BACKUPS
from Services.BackupService import backup_service

load_dotenv()

app = Flask(__name__)

# ============================================
# SELECTOR DE BASE DE DATOS (SOLO UNA VEZ)
# ============================================
def select_database():
    """Pregunta al usuario qué base de datos usar al iniciar"""
    # Verificar si ya se seleccionó antes
    if os.environ.get('DB_SELECTED') == 'true':
        return os.getenv('DB_TYPE', 'mysql')
    
    print("\n" + "="*50)
    print("BIENVENIDO A CRAZY LETTUCES API")
    print("="*50)
    print("\nSELECCIONA LA BASE DE DATOS:")
    print("   1) MySQL")
    print("   2) MongoDB")
    print("   0) Usar la configurada en .env")
    print("-"*50)
    
    while True:
        try:
            choice = input("\nIngresa tu opción (0, 1, 2): ").strip()
            
            if choice == '0':
                db_type = os.getenv('DB_TYPE', 'mysql')
                print(f"Usando configuración de .env: {db_type}")
                break
            elif choice == '1':
                db_type = 'mysql'
                print("Usando MySQL")
                break
            elif choice == '2':
                db_type = 'mongodb'
                print("Usando MongoDB")
                break
            else:
                print("Opción inválida. Intenta de nuevo.")
        except KeyboardInterrupt:
            print("\n\n¡Hasta luego!")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}. Intenta de nuevo.")
    
    # Guardar la selección para que no pregunte de nuevo
    os.environ['DB_SELECTED'] = 'true'
    os.environ['DB_TYPE'] = db_type
    return db_type

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================
# Solo preguntar si no estamos en un reinicio de debug
if not app.debug or not os.environ.get('WERKZEUG_RUN_MAIN'):
    selected_db = select_database()
    # Actualizar la configuración global
    import config
    config.DB_TYPE = selected_db
else:
    # En reinicio de debug, usar lo que ya estaba seleccionado
    selected_db = os.getenv('DB_TYPE', 'mysql')
    print(f"Reiniciando con base de datos: {selected_db}")

# Configuración JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'hola')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

jwt = JWTManager(app)

# Configuración Base de Datos según tipo SELECCIONADO
DB_TYPE = selected_db
print(f"\nInicializando con base de datos: {DB_TYPE.upper()}")

if DB_TYPE == 'mysql':
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db_sql.init_app(app)
    migrate.init_app(app, db_sql)
    print("Conectado a MySQL")
    
    with app.app_context():
        db_sql.create_all()
        print("Tablas verificadas/creadas en MySQL")
else:  # MongoDB
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    db_mongo.init_app(app)
    print("Conectado a MongoDB")
    
    try:
        db_mongo.db.command('ping')
        print("Conexión a MongoDB verificada")
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")

# ============================================
# INICIALIZAR SERVICIOS
# ============================================
# Inicializar el servicio de backups con la aplicación
backup_service.init_app(app)
print("Servicio de backups inicializado")

# Configuración CORS
CORS(app, 
    origins=["http://localhost:3000", "http://localhost:3001", 
            "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Backup-Code", "X-User-Id"],
    expose_headers=["X-Backup-Code", "X-User-Id"],
    supports_credentials=True
)

# Configurar Swagger
app.config['SWAGGER'] = {
    'title': 'API balancea',
    'uiversion': 3,
    'specs_route': '/docs/',
    'specs': [{
        'endpoint': 'apispec_1',
        'route': '/apispec_1.json',
        'rule_filter': lambda rule: True,
        'model_filter': lambda tag: True,
    }],
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    }
}

swagger = Swagger(app)

from Controllers.analisisController import analizar_suplementos

# Registrar la ruta para el análisis con Spark
app.add_url_rule('/suplementos/analisis', 
                 view_func=analizar_suplementos, 
                 methods=['GET'])

# Importar rutas
from Routes.user import user_bp
from Routes.suplementos import suplementos_bp
from Routes.ordenes import orden_bp
from Routes.notificaciones import notificaciones_bp
from Routes.backup import backup_bp
from Routes.direccion import direccion_bp
from Routes.tarjetas import tarjeta_bp
from Routes.dietas import dieta_bp
from Routes.diagramas import diagrama_bp

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(suplementos_bp, url_prefix='/suplementos')
app.register_blueprint(orden_bp, url_prefix='/ordenes')
app.register_blueprint(notificaciones_bp, url_prefix='/notificaciones')
app.register_blueprint(backup_bp, url_prefix='/backups')
app.register_blueprint(direccion_bp, url_prefix='/direcciones')
app.register_blueprint(tarjeta_bp, url_prefix='/tarjetas')
app.register_blueprint(dieta_bp, url_prefix='/dietas')
app.register_blueprint(diagrama_bp, url_prefix='/diagramas')

# Rutas de utilidad
@app.route('/db-info', methods=['GET'])
def db_info():
    return jsonify({
        'db_type': DB_TYPE,
        'status': 'Funcionando correctamente',
        'message': f'Usando base de datos: {DB_TYPE}'
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'message': 'API Crazy Lettuces funcionando correctamente',
        'version': '1.0.0',
        'database': DB_TYPE
    })

@app.route('/routes', methods=['GET'])
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)

# Manejadores de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'msg': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'msg': 'Error interno del servidor'}), 500

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'msg': 'No autorizado'}), 401

if __name__ == '__main__':
    print("\n" + "="*50)
    print(f"Servidor iniciado con {DB_TYPE.upper()}")
    print(f"Documentación: http://localhost:5000/docs")
    print(f"Health check: http://localhost:5000/health")
    print(f"ℹDB Info: http://localhost:5000/db-info")
    print(f"Backup Service: Inicializado")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)