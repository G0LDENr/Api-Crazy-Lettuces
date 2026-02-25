# Models/User.py
from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime
import traceback

# NO instanciar Bcrypt aquí - lo haremos dentro de las funciones que lo necesiten

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class UserSQL(db_sql.Model):
    __tablename__ = 'users'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    nombre = db_sql.Column(db_sql.String(100), nullable=False)
    correo = db_sql.Column(db_sql.String(100), unique=True, nullable=False)
    contraseña = db_sql.Column(db_sql.String(255), nullable=False)
    rol = db_sql.Column(db_sql.Integer, default=2)
    telefono = db_sql.Column(db_sql.String(20), nullable=True)
    sexo = db_sql.Column(db_sql.String(10), nullable=True)
    fecha_registro = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    
    # Relación con direcciones - Usar 'DireccionSQL' en lugar de 'Direccion'
    direcciones = db_sql.relationship('DireccionSQL', back_populates='usuario', lazy=True, cascade='all, delete-orphan')
    
    @property
    def direccion_predeterminada(self):
        """Obtiene la dirección predeterminada del usuario"""
        from Models.Direccion import Direccion
        return Direccion.get_direccion_predeterminada(self.id)
    
    @property
    def direccion_texto(self):
        """Obtiene el texto de la dirección predeterminada"""
        try:
            direccion = self.direccion_predeterminada
            if direccion:
                from Models.Direccion import Direccion
                direccion_dict = Direccion.to_dict(direccion)
                return direccion_dict.get('direccion_completa')
            return None
        except Exception as e:
            print(f"Error en direccion_texto: {e}")
            return None
    
    def __repr__(self):
        return f'<User {self.correo}>'

# ============================================
# REPOSITORIO ÚNICO - Maneja ambas bases de datos
# ============================================
class UserRepository:
    """Repositorio que maneja ambas bases de datos según DB_TYPE"""
    
    def __init__(self):
        from config import DB_TYPE
        self.db_type = DB_TYPE
        # Instanciar Bcrypt dentro del constructor
        from flask_bcrypt import Bcrypt
        self.bcrypt = Bcrypt()
        print(f"🔌 UserRepository inicializado con DB_TYPE: {self.db_type}")
    
    # ============ MÉTODOS DE BÚSQUEDA ============
    
    def find_by_credentials(self, email, password):
        """Buscar usuario por email y verificar contraseña"""
        try:
            email = email.lower().strip()
            
            if self.db_type == 'mysql':
                user = UserSQL.query.filter_by(correo=email).first()
                if user and self.bcrypt.check_password_hash(user.contraseña, password):
                    return user
                return None
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                user = db_mongo.db.users.find_one({'correo': email})
                if user and self.bcrypt.check_password_hash(user['contraseña'], password):
                    return user
                return None
                
        except Exception as e:
            print(f"Error en find_by_credentials: {e}")
            traceback.print_exc()
            return None
    
    def find_by_email(self, email):
        """Buscar usuario por email"""
        try:
            email = email.lower().strip()
            
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(correo=email).first()
            else:  # MongoDB
                return db_mongo.db.users.find_one({'correo': email})
                
        except Exception as e:
            print(f"Error en find_by_email: {e}")
            return None
    
    def find_by_id(self, user_id):
        """Buscar usuario por ID"""
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.get(int(user_id))
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                try:
                    return db_mongo.db.users.find_one({'_id': ObjectId(str(user_id))})
                except:
                    return None
                    
        except Exception as e:
            print(f"Error en find_by_id: {e}")
            return None
    
    def get_all_users(self):
        """Obtener todos los usuarios"""
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.all()
            else:  # MongoDB
                return list(db_mongo.db.users.find())
        except Exception as e:
            print(f"Error en get_all_users: {e}")
            return []
    
    def search_users(self, query):
        """Buscar usuarios por nombre o email"""
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.filter(
                    (UserSQL.nombre.ilike(f'%{query}%')) | 
                    (UserSQL.correo.ilike(f'%{query}%'))
                ).all()
                
            else:  # MongoDB
                import re
                regex = re.compile(f'.*{query}.*', re.IGNORECASE)
                return list(db_mongo.db.users.find({
                    '$or': [
                        {'nombre': {'$regex': regex}},
                        {'correo': {'$regex': regex}}
                    ]
                }))
                
        except Exception as e:
            print(f"Error en search_users: {e}")
            return []
    
    def get_users_by_role(self, role_id):
        """Obtener usuarios por rol"""
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(rol=role_id).all()
            else:  # MongoDB
                return list(db_mongo.db.users.find({'rol': int(role_id)}))
        except Exception as e:
            print(f"Error en get_users_by_role: {e}")
            return []
    
    # ============ MÉTODOS DE CREACIÓN/ACTUALIZACIÓN ============
    
    def create_user(self, user_data):
        """Crear nuevo usuario"""
        try:
            # Hashear contraseña
            hashed_password = self.bcrypt.generate_password_hash(
                user_data['contraseña']
            ).decode('utf-8')
            user_data['contraseña'] = hashed_password
            
            if self.db_type == 'mysql':
                user = UserSQL(
                    nombre=user_data['nombre'],
                    correo=user_data['correo'].lower().strip(),
                    contraseña=user_data['contraseña'],
                    rol=user_data.get('rol', 2),
                    telefono=user_data.get('telefono', ''),
                    sexo=user_data.get('sexo', ''),
                    fecha_registro=user_data.get('fecha_registro', datetime.utcnow())
                )
                db_sql.session.add(user)
                db_sql.session.commit()
                return user.id
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                user_data['correo'] = user_data['correo'].lower().strip()
                user_data['fecha_registro'] = datetime.utcnow()
                result = db_mongo.db.users.insert_one(user_data)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error en create_user: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            traceback.print_exc()
            raise e
    
    def update_user(self, user_id, update_data):
        """Actualizar usuario"""
        try:
            if self.db_type == 'mysql':
                user = UserSQL.query.get(int(user_id))
                if not user:
                    return False
                
                if 'nombre' in update_data:
                    user.nombre = update_data['nombre']
                if 'correo' in update_data:
                    user.correo = update_data['correo'].lower().strip()
                if 'contraseña' in update_data:
                    user.contraseña = self.bcrypt.generate_password_hash(
                        update_data['contraseña']
                    ).decode('utf-8')
                if 'rol' in update_data:
                    user.rol = update_data['rol']
                if 'telefono' in update_data:
                    user.telefono = update_data['telefono']
                if 'sexo' in update_data:
                    user.sexo = update_data['sexo']
                
                db_sql.session.commit()
                return True
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                if 'contraseña' in update_data:
                    update_data['contraseña'] = self.bcrypt.generate_password_hash(
                        update_data['contraseña']
                    ).decode('utf-8')
                
                if 'correo' in update_data:
                    update_data['correo'] = update_data['correo'].lower().strip()
                
                result = db_mongo.db.users.update_one(
                    {'_id': ObjectId(str(user_id))},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_user: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            return False
    
    def delete_user(self, user_id):
        """Eliminar usuario"""
        try:
            if self.db_type == 'mysql':
                user = UserSQL.query.get(int(user_id))
                if not user:
                    return False
                db_sql.session.delete(user)
                db_sql.session.commit()
                return True
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                result = db_mongo.db.users.delete_one({'_id': ObjectId(str(user_id))})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_user: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            return False
    
    # ============ MÉTODOS DE UTILIDAD ============
    
    def to_dict(self, user, include_direcciones=False):
        """Convertir usuario a diccionario según el tipo de DB"""
        try:
            if self.db_type == 'mysql':
                if not user:
                    return None
                
                # Obtener dirección predeterminada
                direccion = None
                try:
                    if hasattr(user, 'direccion_texto'):
                        direccion = user.direccion_texto
                except Exception as e:
                    print(f"⚠️ Error al obtener direccion_texto: {e}")
                
                user_dict = {
                    'id': user.id,
                    'nombre': user.nombre,
                    'correo': user.correo,
                    'rol': user.rol,
                    'rol_texto': self.get_role_name(user.rol),
                    'telefono': user.telefono or '',
                    'sexo': user.sexo or '',
                    'fecha_registro': user.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if user.fecha_registro else None,
                    'direccion': direccion
                }
                
                if include_direcciones:
                    try:
                        from Models.Direccion import Direccion
                        direcciones_list = []
                        for d in user.direcciones:
                            d_dict = Direccion.to_dict(d)
                            if d_dict:
                                direcciones_list.append(d_dict)
                        user_dict['direcciones'] = direcciones_list
                        user_dict['total_direcciones'] = len(direcciones_list)
                        
                        # Buscar dirección predeterminada
                        pred = Direccion.get_direccion_predeterminada(user.id)
                        if pred:
                            user_dict['direccion_predeterminada'] = Direccion.to_dict(pred)
                        else:
                            user_dict['direccion_predeterminada'] = None
                    except Exception as e:
                        print(f"⚠️ Error al obtener direcciones: {e}")
                        user_dict['direcciones'] = []
                        user_dict['total_direcciones'] = 0
                        user_dict['direccion_predeterminada'] = None
                
                return user_dict
                
            else:  # MongoDB
                if not user:
                    return None
                
                from bson.objectid import ObjectId
                user_dict = dict(user)
                user_dict['id'] = str(user_dict.pop('_id'))
                user_dict['rol_texto'] = self.get_role_name(user_dict.get('rol', 2))
                
                # Intentar obtener dirección para MongoDB
                try:
                    from Models.Direccion import Direccion
                    direccion_pred = Direccion.get_direccion_predeterminada(user_dict['id'])
                    if direccion_pred:
                        direccion_dict = Direccion.to_dict(direccion_pred)
                        user_dict['direccion'] = direccion_dict.get('direccion_completa')
                    else:
                        user_dict['direccion'] = None
                except Exception as e:
                    print(f"⚠️ Error obteniendo dirección en MongoDB: {e}")
                    user_dict['direccion'] = None
                
                if 'fecha_registro' in user_dict and user_dict['fecha_registro']:
                    if isinstance(user_dict['fecha_registro'], datetime):
                        user_dict['fecha_registro'] = user_dict['fecha_registro'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Incluir direcciones si se solicita (para MongoDB)
                if include_direcciones:
                    try:
                        from Models.Direccion import Direccion
                        direcciones = list(db_mongo.db.direcciones.find({'user_id': user_dict['id']}))
                        direcciones_list = []
                        for dir_doc in direcciones:
                            dir_dict = Direccion.to_dict(dir_doc)
                            if dir_dict:
                                direcciones_list.append(dir_dict)
                        user_dict['direcciones'] = direcciones_list
                        user_dict['total_direcciones'] = len(direcciones_list)
                        
                        # Buscar dirección predeterminada
                        pred = db_mongo.db.direcciones.find_one({'user_id': user_dict['id'], 'predeterminada': True})
                        if pred:
                            user_dict['direccion_predeterminada'] = Direccion.to_dict(pred)
                        else:
                            user_dict['direccion_predeterminada'] = None
                    except Exception as e:
                        print(f"⚠️ Error al obtener direcciones: {e}")
                        user_dict['direcciones'] = []
                        user_dict['total_direcciones'] = 0
                        user_dict['direccion_predeterminada'] = None
                
                return user_dict
                
        except Exception as e:
            print(f"Error en to_dict: {e}")
            return None
    
    def get_role_name(self, role_id):
        """Obtener nombre del rol por ID"""
        from config import ROLES
        return ROLES.get(role_id, 'client')
    
    def is_valid_role(self, role_id):
        """Verificar si un rol es válido"""
        from config import ROLES
        return role_id in ROLES

# Para facilitar la importación en otros archivos
User = UserSQL  # Alias para compatibilidad