from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime
import traceback
import secrets
import string
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
    
    # NUEVOS CAMPOS PARA CUENTAS INFANTILES
    tipo_cuenta = db_sql.Column(db_sql.String(20), default='personal')
    edad = db_sql.Column(db_sql.Integer, nullable=True)
    tutor_nombre = db_sql.Column(db_sql.String(100), nullable=True)
    tutor_telefono = db_sql.Column(db_sql.String(20), nullable=True)
    restricciones_infantiles = db_sql.Column(db_sql.Text, nullable=True)
    
    # CAMPOS PARA CÓDIGO DE RESPALDO PERMANENTE
    backup_code = db_sql.Column(db_sql.String(50), nullable=True)
    backup_code_generated_at = db_sql.Column(db_sql.DateTime, nullable=True)
    
    # Relaciones
    direcciones = db_sql.relationship('DireccionSQL', back_populates='usuario', lazy=True, cascade='all, delete-orphan')
    tarjetas = db_sql.relationship('TarjetaSQL', back_populates='usuario', lazy=True, cascade='all, delete-orphan')
    
    @property
    def direccion_predeterminada(self):
        from Models.Direccion import Direccion
        return Direccion.get_direccion_predeterminada(self.id)
    
    @property
    def direccion_texto(self):
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
    
    @property
    def tarjeta_predeterminada(self):
        try:
            from Models.Targetas import tarjeta_repo
            return tarjeta_repo.find_predeterminada(self.id)
        except Exception as e:
            print(f"Error en tarjeta_predeterminada: {e}")
            return None
    
    @property
    def tarjeta_enmascarada(self):
        try:
            tarjeta = self.tarjeta_predeterminada
            if tarjeta:
                from Models.Targetas import tarjeta_repo
                tarjeta_dict = tarjeta_repo.to_dict(tarjeta)
                return tarjeta_dict.get('numero_enmascarado')
            return None
        except Exception as e:
            print(f"Error en tarjeta_enmascarada: {e}")
            return None
    
    def __repr__(self):
        return f'<User {self.correo}>'

# ============================================
# REPOSITORIO ÚNICO
# ============================================
class UserRepository:
    """Repositorio que maneja ambas bases de datos según DB_TYPE"""
    
    def __init__(self):
        from config import DB_TYPE
        self.db_type = DB_TYPE
        from flask_bcrypt import Bcrypt
        self.bcrypt = Bcrypt()
        print(f"🔌 UserRepository inicializado con DB_TYPE: {self.db_type}")
    
    # ============ MÉTODOS DE BÚSQUEDA ============
    
    def find_by_credentials(self, email, password):
        try:
            email = email.lower().strip()
            
            if self.db_type == 'mysql':
                user = UserSQL.query.filter_by(correo=email).first()
                if user and self.bcrypt.check_password_hash(user.contraseña, password):
                    return user
                return None
                
            else:
                user = db_mongo.db.users.find_one({'correo': email})
                if user and self.bcrypt.check_password_hash(user['contraseña'], password):
                    return user
                return None
                
        except Exception as e:
            print(f"Error en find_by_credentials: {e}")
            traceback.print_exc()
            return None
    
    def find_by_email(self, email):
        try:
            email = email.lower().strip()
            
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(correo=email).first()
            else:
                return db_mongo.db.users.find_one({'correo': email})
                
        except Exception as e:
            print(f"Error en find_by_email: {e}")
            return None
    
    def find_by_phone(self, telefono):
        try:
            if not telefono:
                return None
                
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(telefono=telefono).first()
            else:
                return db_mongo.db.users.find_one({'telefono': telefono})
                
        except Exception as e:
            print(f"Error en find_by_phone: {e}")
            return None
    
    def find_by_id(self, user_id):
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.get(int(user_id))
                
            else:
                from bson.objectid import ObjectId
                try:
                    return db_mongo.db.users.find_one({'_id': ObjectId(str(user_id))})
                except:
                    return None
                    
        except Exception as e:
            print(f"Error en find_by_id: {e}")
            return None
    
    def find_children_by_tutor(self, tutor_telefono):
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(tutor_telefono=tutor_telefono).all()
            else:
                return list(db_mongo.db.users.find({'tutor_telefono': tutor_telefono}))
        except Exception as e:
            print(f"Error en find_children_by_tutor: {e}")
            return []
    
    def get_all_users(self):
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.all()
            else:
                return list(db_mongo.db.users.find())
        except Exception as e:
            print(f"Error en get_all_users: {e}")
            return []
    
    def search_users(self, query):
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.filter(
                    (UserSQL.nombre.ilike(f'%{query}%')) | 
                    (UserSQL.correo.ilike(f'%{query}%'))
                ).all()
                
            else:
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
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(rol=role_id).all()
            else:
                return list(db_mongo.db.users.find({'rol': int(role_id)}))
        except Exception as e:
            print(f"Error en get_users_by_role: {e}")
            return []
    
    def get_users_by_tipo_cuenta(self, tipo_cuenta):
        try:
            if self.db_type == 'mysql':
                return UserSQL.query.filter_by(tipo_cuenta=tipo_cuenta).all()
            else:
                return list(db_mongo.db.users.find({'tipo_cuenta': tipo_cuenta}))
        except Exception as e:
            print(f"Error en get_users_by_tipo_cuenta: {e}")
            return []
    
    # ============ MÉTODOS DE CREACIÓN/ACTUALIZACIÓN ============
    
    def create_user(self, user_data):
        try:
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
                    fecha_registro=user_data.get('fecha_registro', datetime.utcnow()),
                    tipo_cuenta=user_data.get('tipo_cuenta', 'personal'),
                    edad=user_data.get('edad'),
                    tutor_nombre=user_data.get('tutor_nombre'),
                    tutor_telefono=user_data.get('tutor_telefono'),
                    restricciones_infantiles=user_data.get('restricciones_infantiles')
                )
                db_sql.session.add(user)
                db_sql.session.commit()
                return user.id
                
            else:
                user_data['correo'] = user_data['correo'].lower().strip()
                user_data['fecha_registro'] = datetime.utcnow()
                user_data['tipo_cuenta'] = user_data.get('tipo_cuenta', 'personal')
                
                result = db_mongo.db.users.insert_one(user_data)
                return str(result.inserted_id)
                
        except Exception as e:
            print(f"Error en create_user: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            traceback.print_exc()
            raise e
    
    def update_user(self, user_id, update_data):
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
                if 'tipo_cuenta' in update_data:
                    user.tipo_cuenta = update_data['tipo_cuenta']
                if 'edad' in update_data:
                    user.edad = update_data['edad']
                if 'tutor_nombre' in update_data:
                    user.tutor_nombre = update_data['tutor_nombre']
                if 'tutor_telefono' in update_data:
                    user.tutor_telefono = update_data['tutor_telefono']
                if 'restricciones_infantiles' in update_data:
                    user.restricciones_infantiles = update_data['restricciones_infantiles']
                if 'backup_code' in update_data:
                    user.backup_code = update_data['backup_code']
                if 'backup_code_generated_at' in update_data:
                    user.backup_code_generated_at = update_data['backup_code_generated_at']
                
                db_sql.session.commit()
                return True
                
            else:
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
        try:
            if self.db_type == 'mysql':
                user = UserSQL.query.get(int(user_id))
                if not user:
                    return False
                db_sql.session.delete(user)
                db_sql.session.commit()
                return True
                
            else:
                from bson.objectid import ObjectId
                result = db_mongo.db.users.delete_one({'_id': ObjectId(str(user_id))})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_user: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            return False
    
    # ============ MÉTODOS PARA CÓDIGO DE RESPALDO PERMANENTE ============
    
    def generate_backup_code(self, user_id):
        """Generar un código único PERMANENTE para respaldos (no se invalida)"""
        try:
            alphabet = string.ascii_letters + string.digits
            raw_code = ''.join(secrets.choice(alphabet) for _ in range(16))
            
            update_data = {
                'backup_code': raw_code,
                'backup_code_generated_at': datetime.utcnow()
            }
            
            if self.update_user(user_id, update_data):
                return raw_code
            return None
            
        except Exception as e:
            print(f"Error generando código: {e}")
            return None
    
    def verify_backup_code(self, user_id, code):
        """Verificar código de respaldo PERMANENTE (case-insensitive)"""
        try:
            if not code:
                return False
                
            if self.db_type == 'mysql':
                user = UserSQL.query.get(int(user_id))
                if not user or not user.backup_code:
                    return False
                
                # Comparar sin distinguir mayúsculas/minúsculas
                return user.backup_code.lower() == code.lower()
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                user = db_mongo.db.users.find_one({'_id': ObjectId(str(user_id))})
                if not user or not user.get('backup_code'):
                    return False
                
                # Comparar sin distinguir mayúsculas/minúsculas
                return user.get('backup_code').lower() == code.lower()
                    
        except Exception as e:
            print(f"Error verificando código: {e}")
            return False
    
    def has_valid_backup_code(self, user_id):
        """Verificar si el usuario tiene un código válido"""
        try:
            if self.db_type == 'mysql':
                user = UserSQL.query.get(int(user_id))
                return user and user.backup_code is not None
            else:
                from bson.objectid import ObjectId
                user = db_mongo.db.users.find_one({'_id': ObjectId(str(user_id))})
                return user and user.get('backup_code') is not None
        except Exception as e:
            print(f"Error verificando código: {e}")
            return False
    
    # ============ MÉTODOS DE UTILIDAD ============
    
    def to_dict(self, user, include_direcciones=False, include_tarjetas=False, include_ninos=False):
        """Convertir usuario a diccionario según el tipo de DB"""
        try:
            if self.db_type == 'mysql':
                if not user:
                    return None
                
                direccion = None
                try:
                    if hasattr(user, 'direccion_texto'):
                        direccion = user.direccion_texto
                except Exception as e:
                    print(f"⚠️ Error al obtener direccion_texto: {e}")
                
                tarjeta = None
                try:
                    if hasattr(user, 'tarjeta_enmascarada'):
                        tarjeta = user.tarjeta_enmascarada
                except Exception as e:
                    print(f"⚠️ Error al obtener tarjeta_enmascarada: {e}")
                
                user_dict = {
                    'id': user.id,
                    'nombre': user.nombre,
                    'correo': user.correo,
                    'rol': user.rol,
                    'rol_texto': self.get_role_name(user.rol),
                    'telefono': user.telefono or '',
                    'sexo': user.sexo or '',
                    'fecha_registro': user.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if user.fecha_registro else None,
                    'direccion': direccion,
                    'tarjeta': tarjeta,
                    'tipo_cuenta': user.tipo_cuenta,
                    'edad': user.edad,
                    'tutor_nombre': user.tutor_nombre,
                    'tutor_telefono': user.tutor_telefono,
                    'restricciones_infantiles': user.restricciones_infantiles,
                    'has_backup_code': user.backup_code is not None
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
                
                if include_tarjetas:
                    try:
                        from Models.Targetas import tarjeta_repo
                        tarjetas_list = []
                        for t in user.tarjetas:
                            t_dict = tarjeta_repo.to_dict(t)
                            if t_dict:
                                tarjetas_list.append(t_dict)
                        user_dict['tarjetas'] = tarjetas_list
                        user_dict['total_tarjetas'] = len(tarjetas_list)
                        
                        tarjeta_pred = tarjeta_repo.find_predeterminada(user.id)
                        if tarjeta_pred:
                            user_dict['tarjeta_predeterminada'] = tarjeta_repo.to_dict(tarjeta_pred)
                        else:
                            user_dict['tarjeta_predeterminada'] = None
                    except Exception as e:
                        print(f"⚠️ Error al obtener tarjetas: {e}")
                        user_dict['tarjetas'] = []
                        user_dict['total_tarjetas'] = 0
                        user_dict['tarjeta_predeterminada'] = None
                
                if include_ninos and user.tipo_cuenta == 'personal':
                    try:
                        if user.telefono:
                            ninos = self.find_children_by_tutor(user.telefono)
                            ninos_list = [self.to_dict(nino) for nino in ninos]
                            user_dict['ninos'] = ninos_list
                            user_dict['total_ninos'] = len(ninos_list)
                        else:
                            user_dict['ninos'] = []
                            user_dict['total_ninos'] = 0
                    except Exception as e:
                        print(f"⚠️ Error al obtener niños: {e}")
                        user_dict['ninos'] = []
                        user_dict['total_ninos'] = 0
                
                return user_dict
                
            else:
                if not user:
                    return None
                
                from bson.objectid import ObjectId
                user_dict = dict(user)
                user_dict['id'] = str(user_dict.pop('_id'))
                user_dict['rol_texto'] = self.get_role_name(user_dict.get('rol', 2))
                
                if 'tipo_cuenta' not in user_dict:
                    user_dict['tipo_cuenta'] = 'personal'
                
                user_dict['has_backup_code'] = user_dict.get('backup_code') is not None
                
                try:
                    from Models.Direccion import Direccion
                    direccion_pred = Direccion.get_direccion_predeterminada(user_dict['id'])
                    if direccion_pred:
                        direccion_dict = Direccion.to_dict(direccion_pred)
                        user_dict['direccion'] = direccion_dict.get('direccion_completa')
                    else:
                        user_dict['direccion'] = None
                except Exception as e:
                    print(f"⚠️ Error obteniendo dirección: {e}")
                    user_dict['direccion'] = None
                
                try:
                    from Models.Targetas import tarjeta_repo
                    tarjeta_pred = tarjeta_repo.find_predeterminada(user_dict['id'])
                    if tarjeta_pred:
                        tarjeta_dict = tarjeta_repo.to_dict(tarjeta_pred)
                        user_dict['tarjeta'] = tarjeta_dict.get('numero_enmascarado')
                    else:
                        user_dict['tarjeta'] = None
                except Exception as e:
                    print(f"⚠️ Error obteniendo tarjeta: {e}")
                    user_dict['tarjeta'] = None
                
                if 'fecha_registro' in user_dict and user_dict['fecha_registro']:
                    if isinstance(user_dict['fecha_registro'], datetime):
                        user_dict['fecha_registro'] = user_dict['fecha_registro'].strftime('%Y-%m-%d %H:%M:%S')
                
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
                
                if include_tarjetas:
                    try:
                        from Models.Targetas import tarjeta_repo
                        tarjetas = list(db_mongo.db.tarjetas.find({'user_id': user_dict['id']}))
                        tarjetas_list = []
                        for t_doc in tarjetas:
                            t_dict = tarjeta_repo.to_dict(t_doc)
                            if t_dict:
                                tarjetas_list.append(t_dict)
                        user_dict['tarjetas'] = tarjetas_list
                        user_dict['total_tarjetas'] = len(tarjetas_list)
                        
                        tarjeta_pred = db_mongo.db.tarjetas.find_one({'user_id': user_dict['id'], 'predeterminada': True})
                        if tarjeta_pred:
                            user_dict['tarjeta_predeterminada'] = tarjeta_repo.to_dict(tarjeta_pred)
                        else:
                            user_dict['tarjeta_predeterminada'] = None
                    except Exception as e:
                        print(f"⚠️ Error al obtener tarjetas: {e}")
                        user_dict['tarjetas'] = []
                        user_dict['total_tarjetas'] = 0
                        user_dict['tarjeta_predeterminada'] = None
                
                if include_ninos and user_dict.get('tipo_cuenta') == 'personal':
                    try:
                        if user_dict.get('telefono'):
                            ninos = list(db_mongo.db.users.find({'tutor_telefono': user_dict['telefono']}))
                            ninos_list = [self.to_dict(nino) for nino in ninos]
                            user_dict['ninos'] = ninos_list
                            user_dict['total_ninos'] = len(ninos_list)
                        else:
                            user_dict['ninos'] = []
                            user_dict['total_ninos'] = 0
                    except Exception as e:
                        print(f"⚠️ Error al obtener niños: {e}")
                        user_dict['ninos'] = []
                        user_dict['total_ninos'] = 0
                
                return user_dict
                
        except Exception as e:
            print(f"Error en to_dict: {e}")
            traceback.print_exc()
            return None
    
    def get_role_name(self, role_id):
        from config import ROLES
        return ROLES.get(role_id, 'client')
    
    def is_valid_role(self, role_id):
        from config import ROLES
        return role_id in ROLES

# ============================================
# INSTANCIA GLOBAL
# ============================================
user_repo = UserRepository()
User = UserSQL