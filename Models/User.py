from config import db
from flask_bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt()

# Sistema de roles (fácil de expandir)
ROLES = {
    1: 'admin',
    2: 'client',
}

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Integer, default=2)  # Usa números para los roles
    telefono = db.Column(db.String(20), nullable=True)
    sexo = db.Column(db.String(10), nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Métodos para manejar roles
    @classmethod
    def get_roles(cls):
        """Obtener diccionario de roles disponibles"""
        return ROLES
    
    @classmethod
    def add_role(cls, role_id, role_name):
        """Agregar nuevo rol (para expansión futura)"""
        global ROLES
        ROLES[role_id] = role_name
    
    @classmethod
    def get_role_name(cls, role_id):
        """Obtener nombre del rol por ID"""
        return ROLES.get(role_id, 'client')
    
    @classmethod
    def get_role_id(cls, role_name):
        """Obtener ID del rol por nombre"""
        for role_id, name in ROLES.items():
            if name == role_name:
                return role_id
        return 2  # Default client
    
    @classmethod
    def is_valid_role(cls, role_id):
        """Verificar si un rol es válido"""
        return role_id in ROLES
    
    @classmethod
    def find_by_credentials(cls, email, password):
        """Buscar usuario por email y verificar contraseña"""
        user = cls.query.filter_by(correo=email.lower().strip()).first()
        if user and bcrypt.check_password_hash(user.contraseña, password):
            return user
        return None
    
    @classmethod
    def find_by_email(cls, email):
        """Buscar usuario por email"""
        return cls.query.filter_by(correo=email.lower().strip()).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        """Buscar usuario por ID"""
        return cls.query.get(user_id)
    
    @classmethod
    def get_all_users(cls):
        """Obtener todos los usuarios"""
        return cls.query.all()
    
    @classmethod
    def create_user(cls, user_data):
        """Crear nuevo usuario"""
        # Validar rol
        rol = user_data.get('rol', 2)
        if not cls.is_valid_role(rol):
            rol = 2  # Default client
        
        # Hashear contraseña
        hashed_password = bcrypt.generate_password_hash(
            user_data['contraseña']
        ).decode('utf-8')
        
        user = cls(
            nombre=user_data['nombre'],
            correo=user_data['correo'],
            contraseña=hashed_password,
            rol=rol,
            telefono=user_data.get('telefono', ''),
            sexo=user_data.get('sexo', '')
        )
        
        db.session.add(user)
        db.session.commit()
        return user.id
    
    @classmethod
    def update_user(cls, user_id, update_data):
        """Actualizar usuario"""
        user = cls.query.get(user_id)
        if not user:
            return False
        
        if 'nombre' in update_data:
            user.nombre = update_data['nombre']
        if 'correo' in update_data:
            user.correo = update_data['correo']
        if 'contraseña' in update_data:
            user.contraseña = bcrypt.generate_password_hash(
                update_data['contraseña']
            ).decode('utf-8')
        if 'rol' in update_data:
            # Validar el nuevo rol
            if cls.is_valid_role(update_data['rol']):
                user.rol = update_data['rol']
        if 'telefono' in update_data:
            user.telefono = update_data['telefono']
        if 'sexo' in update_data:
            user.sexo = update_data['sexo']
        
        db.session.commit()
        return True
    
    @classmethod
    def delete_user(cls, user_id):
        """Eliminar usuario"""
        try:
            print(f"🔍 DEBUG MODELO - Iniciando eliminación del usuario ID: {user_id}")
            
            user = cls.query.get(user_id)
            print(f"🔍 DEBUG MODELO - Usuario encontrado: {user is not None}")
            
            if not user:
                print(f"❌ DEBUG MODELO - Usuario {user_id} no encontrado en la base de datos")
                return False
            
            print(f"🔍 DEBUG MODELO - Datos del usuario a eliminar:")
            print(f"   ID: {user.id}")
            print(f"   Nombre: {user.nombre}")
            print(f"   Email: {user.correo}")
            print(f"   Rol: {user.rol}")
            
            # Intentar eliminar el usuario
            db.session.delete(user)
            db.session.commit()
            
            print(f"✅ DEBUG MODELO - Usuario {user_id} eliminado exitosamente de la base de datos")
            return True
            
        except Exception as error:
            print(f"💥 DEBUG MODELO - Error al eliminar usuario {user_id}: {str(error)}")
            print(f"💥 DEBUG MODELO - Tipo de error: {type(error).__name__}")
            db.session.rollback()  # Importante: hacer rollback en caso de error
            return False
    
    @classmethod
    def search_users(cls, query):
        """Buscar usuarios por nombre o email"""
        if query:
            return cls.query.filter(
                (cls.nombre.ilike(f'%{query}%')) | 
                (cls.correo.ilike(f'%{query}%'))
            ).all()
        return cls.query.all()
    
    @classmethod
    def get_users_by_role(cls, role_id):
        """Obtener usuarios por rol"""
        if not cls.is_valid_role(role_id):
            return []
        return cls.query.filter_by(rol=role_id).all()
    
    @classmethod
    def to_dict(cls, user):
        """Convertir objeto usuario a diccionario para JSON"""
        if not user:
            return None
        
        return {
            'id': user.id,
            'nombre': user.nombre,
            'correo': user.correo,
            'telefono': getattr(user, 'telefono', ''),
            'sexo': getattr(user, 'sexo', ''),
            'rol': user.rol,
            'rol_texto': cls.get_role_name(user.rol) if hasattr(cls, 'get_role_name') else ('admin' if user.rol == 1 else 'cliente'),
            'fecha_registro': user.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if user.fecha_registro else None
    }