from config import DB_TYPE, db_sql, db_mongo
from datetime import datetime
import traceback
import re

# ============================================
# MODELO PARA MySQL (SQLAlchemy)
# ============================================
class TarjetaSQL(db_sql.Model):
    __tablename__ = 'tarjetas'
    
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    user_id = db_sql.Column(db_sql.Integer, db_sql.ForeignKey('users.id'), nullable=False)
    nombre_titular = db_sql.Column(db_sql.String(100), nullable=False)
    numero_tarjeta = db_sql.Column(db_sql.String(255), nullable=False)  # Encriptado
    numero_enmascarado = db_sql.Column(db_sql.String(20), nullable=False)
    mes_expiracion = db_sql.Column(db_sql.String(2), nullable=False)
    anio_expiracion = db_sql.Column(db_sql.String(4), nullable=False)
    tipo_tarjeta = db_sql.Column(db_sql.String(20), nullable=False)  # visa, mastercard, etc.
    predeterminada = db_sql.Column(db_sql.Boolean, default=False)
    fecha_registro = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    
    # Relación con usuario
    usuario = db_sql.relationship('UserSQL', back_populates='tarjetas')
    
    def __repr__(self):
        return f'<Tarjeta {self.numero_enmascarado}>'

# ============================================
# REPOSITORIO DE TARJETAS
# ============================================
class TarjetaRepository:
    """Repositorio que maneja ambas bases de datos según DB_TYPE"""
    
    def __init__(self):
        from config import DB_TYPE
        self.db_type = DB_TYPE
        print(f"🔌 TarjetaRepository inicializado con DB_TYPE: {self.db_type}")
    
    # ============ MÉTODOS DE UTILIDAD ============
    
    def enmascarar_numero(self, numero):
        """Enmascara un número de tarjeta (**** **** **** 1234)"""
        try:
            # Limpiar el número (quitar espacios y guiones)
            numero_limpio = re.sub(r'[\s\-]', '', numero)
            
            # Tomar últimos 4 dígitos
            ultimos_cuatro = numero_limpio[-4:]
            
            return f"**** **** **** {ultimos_cuatro}"
        except:
            return "**** **** **** ****"
    
    def detectar_tipo_tarjeta(self, numero):
        """Detecta el tipo de tarjeta por el prefijo"""
        try:
            # Limpiar el número
            numero_limpio = re.sub(r'[\s\-]', '', numero)
            
            # VISA empieza con 4
            if numero_limpio.startswith('4'):
                return 'visa'
            # MasterCard empieza con 51-55
            elif numero_limpio.startswith(('51', '52', '53', '54', '55')):
                return 'mastercard'
            # American Express empieza con 34 o 37
            elif numero_limpio.startswith(('34', '37')):
                return 'amex'
            else:
                return 'otra'
        except:
            return 'otra'
    
    # ============ MÉTODOS DE BÚSQUEDA ============
    
    def find_by_id(self, tarjeta_id):
        """Buscar tarjeta por ID"""
        try:
            if self.db_type == 'mysql':
                return TarjetaSQL.query.get(int(tarjeta_id))
            else:  # MongoDB
                from bson.objectid import ObjectId
                try:
                    return db_mongo.db.tarjetas.find_one({'_id': ObjectId(str(tarjeta_id))})
                except:
                    return None
        except Exception as e:
            print(f"Error en find_by_id (tarjeta): {e}")
            return None
    
    def find_by_user(self, user_id):
        """Buscar tarjetas por usuario"""
        try:
            if self.db_type == 'mysql':
                return TarjetaSQL.query.filter_by(user_id=int(user_id)).all()
            else:  # MongoDB
                cursor = db_mongo.db.tarjetas.find({'user_id': str(user_id)})
                return list(cursor)
        except Exception as e:
            print(f"Error en find_by_user: {e}")
            return []
    
    def find_predeterminada(self, user_id):
        """Buscar tarjeta predeterminada del usuario"""
        try:
            if self.db_type == 'mysql':
                return TarjetaSQL.query.filter_by(user_id=int(user_id), predeterminada=True).first()
            else:  # MongoDB
                return db_mongo.db.tarjetas.find_one({'user_id': str(user_id), 'predeterminada': True})
        except Exception as e:
            print(f"Error en find_predeterminada: {e}")
            return None
    
    # ============ MÉTODOS DE CREACIÓN/ACTUALIZACIÓN ============
    
    def create_tarjeta(self, user_id, tarjeta_data):
        """Crear nueva tarjeta"""
        try:
            from flask_bcrypt import Bcrypt
            bcrypt = Bcrypt()
            
            # Validar datos requeridos
            required_fields = ['nombre_titular', 'numero_tarjeta', 'mes_expiracion', 'anio_expiracion']
            for field in required_fields:
                if not tarjeta_data.get(field):
                    raise ValueError(f"Campo requerido: {field}")
            
            # Validar mes y año
            mes = str(tarjeta_data['mes_expiracion']).strip()
            anio = str(tarjeta_data['anio_expiracion']).strip()
            
            if not mes.isdigit() or int(mes) < 1 or int(mes) > 12:
                raise ValueError("Mes de expiración inválido")
            
            if not anio.isdigit() or len(anio) != 4:
                raise ValueError("Año de expiración inválido")
            
            # Validar número de tarjeta
            numero = re.sub(r'[\s\-]', '', tarjeta_data['numero_tarjeta'])
            if not numero.isdigit() or len(numero) < 13 or len(numero) > 19:
                raise ValueError("Número de tarjeta inválido")
            
            # Enmascarar número
            numero_enmascarado = self.enmascarar_numero(numero)
            
            # Detectar tipo de tarjeta
            tipo_tarjeta = self.detectar_tipo_tarjeta(numero)
            
            # Encriptar número de tarjeta
            numero_encriptado = bcrypt.generate_password_hash(numero).decode('utf-8')
            
            # Verificar si es la primera tarjeta (será predeterminada)
            tarjetas_existentes = self.find_by_user(user_id)
            es_predeterminada = tarjeta_data.get('predeterminada', len(tarjetas_existentes) == 0)
            
            # Si esta tarjeta será predeterminada, quitar predeterminada de las otras
            if es_predeterminada:
                self.remove_default_from_all(user_id)
            
            if self.db_type == 'mysql':
                tarjeta = TarjetaSQL(
                    user_id=int(user_id),
                    nombre_titular=tarjeta_data['nombre_titular'],
                    numero_tarjeta=numero_encriptado,
                    numero_enmascarado=numero_enmascarado,
                    mes_expiracion=mes,
                    anio_expiracion=anio,
                    tipo_tarjeta=tipo_tarjeta,
                    predeterminada=es_predeterminada,
                    fecha_registro=datetime.utcnow()
                )
                db_sql.session.add(tarjeta)
                db_sql.session.commit()
                return tarjeta.id
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                tarjeta_doc = {
                    'user_id': str(user_id),
                    'nombre_titular': tarjeta_data['nombre_titular'],
                    'numero_tarjeta': numero_encriptado,
                    'numero_enmascarado': numero_enmascarado,
                    'mes_expiracion': mes,
                    'anio_expiracion': anio,
                    'tipo_tarjeta': tipo_tarjeta,
                    'predeterminada': es_predeterminada,
                    'fecha_registro': datetime.utcnow()
                }
                result = db_mongo.db.tarjetas.insert_one(tarjeta_doc)
                return str(result.inserted_id)
                
        except ValueError as ve:
            print(f"Error de validación en create_tarjeta: {ve}")
            raise ve
        except Exception as e:
            print(f"Error en create_tarjeta: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            traceback.print_exc()
            raise e
    
    def remove_default_from_all(self, user_id):
        """Quitar predeterminada de todas las tarjetas del usuario"""
        try:
            if self.db_type == 'mysql':
                TarjetaSQL.query.filter_by(user_id=int(user_id)).update({'predeterminada': False})
                db_sql.session.commit()
            else:  # MongoDB
                db_mongo.db.tarjetas.update_many(
                    {'user_id': str(user_id)},
                    {'$set': {'predeterminada': False}}
                )
            return True
        except Exception as e:
            print(f"Error en remove_default_from_all: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            return False
    
    def update_tarjeta(self, tarjeta_id, update_data):
        """Actualizar tarjeta"""
        try:
            if self.db_type == 'mysql':
                tarjeta = TarjetaSQL.query.get(int(tarjeta_id))
                if not tarjeta:
                    return False
                
                if 'nombre_titular' in update_data:
                    tarjeta.nombre_titular = update_data['nombre_titular']
                if 'mes_expiracion' in update_data:
                    tarjeta.mes_expiracion = update_data['mes_expiracion']
                if 'anio_expiracion' in update_data:
                    tarjeta.anio_expiracion = update_data['anio_expiracion']
                if 'predeterminada' in update_data:
                    # Si se marca como predeterminada, quitar de las otras
                    if update_data['predeterminada']:
                        self.remove_default_from_all(tarjeta.user_id)
                    tarjeta.predeterminada = update_data['predeterminada']
                
                db_sql.session.commit()
                return True
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                
                # Si se marca como predeterminada, quitar de las otras
                if update_data.get('predeterminada'):
                    tarjeta = self.find_by_id(tarjeta_id)
                    if tarjeta:
                        tarjeta_dict = self.to_dict(tarjeta)
                        self.remove_default_from_all(tarjeta_dict['user_id'])
                
                result = db_mongo.db.tarjetas.update_one(
                    {'_id': ObjectId(str(tarjeta_id))},
                    {'$set': update_data}
                )
                return result.modified_count > 0
                
        except Exception as e:
            print(f"Error en update_tarjeta: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            return False
    
    def delete_tarjeta(self, tarjeta_id):
        """Eliminar tarjeta"""
        try:
            if self.db_type == 'mysql':
                tarjeta = TarjetaSQL.query.get(int(tarjeta_id))
                if not tarjeta:
                    return False
                db_sql.session.delete(tarjeta)
                db_sql.session.commit()
                return True
                
            else:  # MongoDB
                from bson.objectid import ObjectId
                result = db_mongo.db.tarjetas.delete_one({'_id': ObjectId(str(tarjeta_id))})
                return result.deleted_count > 0
                
        except Exception as e:
            print(f"Error en delete_tarjeta: {e}")
            if self.db_type == 'mysql':
                db_sql.session.rollback()
            return False
    
    # ============ MÉTODOS DE CONVERSIÓN ============
    
    def to_dict(self, tarjeta):
        """Convertir tarjeta a diccionario"""
        try:
            if self.db_type == 'mysql':
                if not tarjeta:
                    return None
                
                return {
                    'id': tarjeta.id,
                    'user_id': tarjeta.user_id,
                    'nombre_titular': tarjeta.nombre_titular,
                    'numero_enmascarado': tarjeta.numero_enmascarado,
                    'mes_expiracion': tarjeta.mes_expiracion,
                    'anio_expiracion': tarjeta.anio_expiracion,
                    'tipo_tarjeta': tarjeta.tipo_tarjeta,
                    'predeterminada': tarjeta.predeterminada,
                    'fecha_registro': tarjeta.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if tarjeta.fecha_registro else None
                }
                
            else:  # MongoDB
                if not tarjeta:
                    return None
                
                from bson.objectid import ObjectId
                tarjeta_dict = dict(tarjeta)
                tarjeta_dict['id'] = str(tarjeta_dict.pop('_id'))
                
                if 'fecha_registro' in tarjeta_dict and tarjeta_dict['fecha_registro']:
                    if isinstance(tarjeta_dict['fecha_registro'], datetime):
                        tarjeta_dict['fecha_registro'] = tarjeta_dict['fecha_registro'].strftime('%Y-%m-%d %H:%M:%S')
                
                return tarjeta_dict
                
        except Exception as e:
            print(f"Error en to_dict (tarjeta): {e}")
            return None

# Instancia global
tarjeta_repo = TarjetaRepository()