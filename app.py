from flask import Flask
from config import db, migrate
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from Services.BackupService import backup_service

load_dotenv()

app = Flask(__name__)

# Configuración JWT - SIN EXPIRACIÓN (token permanente)
app.config['JWT_SECRET_KEY'] = "hola"
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # ¡IMPORTANTE! Token nunca expira

jwt = JWTManager(app)

# Configuración Base de Datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar DB y migraciones
db.init_app(app)
migrate.init_app(app, db)

# Inicializar el servicio de respaldos
backup_service.init_app(app)

# CONFIGURACIÓN CORS MÁS ESPECÍFICA
CORS(app, 
    origins=["http://localhost:3000","http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    supports_credentials=True
)

# Configurar Swagger
app.config['SWAGGER'] = {
    'title': 'API Crazy Lettuces',
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

# Rutas
from Routes.user import user_bp
from Routes.especiales import especiales_bp
from Routes.ordenes import orden_bp
from Routes.notificaciones import notificaciones_bp
from Routes.backup import backup_bp
from Routes.ingredientes import ingredientes_bp
from Routes.direccion import direccion_bp


app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(especiales_bp, url_prefix='/especiales')
app.register_blueprint(orden_bp, url_prefix='/ordenes')
app.register_blueprint(notificaciones_bp, url_prefix='/notificaciones')
app.register_blueprint(backup_bp, url_prefix='/backups')
app.register_blueprint(ingredientes_bp, url_prefix='/ingredientes')
app.register_blueprint(direccion_bp, url_prefix='/direcciones')

if __name__ == '__main__':
    app.run(debug=True)