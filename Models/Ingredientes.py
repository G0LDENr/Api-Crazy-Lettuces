from config import db
from datetime import datetime

class Ingrediente(db.Model):
    __tablename__ = 'ingredientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    categoria = db.Column(db.String(50), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def find_by_id(cls, ingrediente_id):
        """Buscar ingrediente por ID"""
        return cls.query.get(ingrediente_id)
    
    @classmethod
    def find_by_name(cls, nombre):
        """Buscar ingrediente por nombre"""
        return cls.query.filter_by(nombre=nombre).first()
    
    @classmethod
    def get_all_ingredientes(cls, only_active=True, categoria=None):
        """Obtener todos los ingredientes"""
        query = cls.query
        
        if only_active:
            query = query.filter_by(activo=True)
        
        if categoria:
            query = query.filter_by(categoria=categoria)
        
        return query.order_by(cls.nombre.asc()).all()
    
    @classmethod
    def get_ingredientes_activos(cls):
        """Obtener solo ingredientes activos"""
        return cls.query.filter_by(activo=True).order_by(cls.nombre.asc()).all()
    
    @classmethod
    def create_ingrediente(cls, ingrediente_data):
        """Crear nuevo ingrediente"""
        ingrediente = cls(
            nombre=ingrediente_data['nombre'],
            categoria=ingrediente_data.get('categoria'),
            activo=ingrediente_data.get('activo', True)
        )
        
        db.session.add(ingrediente)
        db.session.commit()
        return ingrediente.id
    
    @classmethod
    def update_ingrediente(cls, ingrediente_id, update_data):
        """Actualizar ingrediente"""
        ingrediente = cls.query.get(ingrediente_id)
        if not ingrediente:
            return False
        
        if 'nombre' in update_data:
            ingrediente.nombre = update_data['nombre']
        if 'categoria' in update_data:
            ingrediente.categoria = update_data['categoria']
        if 'activo' in update_data:
            ingrediente.activo = update_data['activo']
        
        ingrediente.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        
        # Si se está desactivando, enviar notificaciones
        if 'activo' in update_data and update_data['activo'] == False:
            cls._enviar_notificaciones_desactivacion(ingrediente_id)
        
        return True
    
    @classmethod
    def delete_ingrediente(cls, ingrediente_id):
        """Eliminar ingrediente (eliminación física)"""
        try:
            ingrediente = cls.query.get(ingrediente_id)
            if not ingrediente:
                return False
            
            db.session.delete(ingrediente)
            db.session.commit()
            return True
            
        except Exception as error:
            print(f"Error al eliminar ingrediente {ingrediente_id}: {str(error)}")
            db.session.rollback()
            return False
    
    @classmethod
    def toggle_activo(cls, ingrediente_id):
        """Activar/desactivar ingrediente"""
        ingrediente = cls.query.get(ingrediente_id)
        if not ingrediente:
            return False
        
        # Guardar estado anterior
        estado_anterior = ingrediente.activo
        
        # Cambiar estado
        ingrediente.activo = not ingrediente.activo
        ingrediente.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        
        # Si se está DESACTIVANDO (de True a False), enviar notificaciones
        if estado_anterior == True and ingrediente.activo == False:
            cls._enviar_notificaciones_desactivacion(ingrediente_id)
        
        return True
    
    @classmethod
    def _enviar_notificaciones_desactivacion(cls, ingrediente_id):
        """
        Enviar notificaciones cuando un ingrediente se desactiva
        Método interno - se llama automáticamente desde toggle_activo y update_ingrediente
        """
        try:
            from Models.Notificaciones import Notificacion
            from Models.User import User
            from Models.Especiales import Especial
            
            ingrediente = cls.find_by_id(ingrediente_id)
            if not ingrediente:
                return False
            
            print(f"\n🔔 [NOTIFICACIONES] ========== INGREDIENTE DESACTIVADO ==========")
            print(f"📦 Ingrediente: {ingrediente.nombre}")
            print(f"🆔 ID: {ingrediente.id}")
            
            # 1. Buscar especiales activos que contengan este ingrediente
            especiales_afectados = []
            todos_especiales = Especial.query.filter_by(activo=True).all()
            
            print(f"🔍 Buscando especiales activos...")
            
            for especial in todos_especiales:
                try:
                    if especial.ingredientes and ingrediente.nombre:
                        ingredientes_especial = especial.ingredientes.lower()
                        ingrediente_nombre = ingrediente.nombre.lower()
                        
                        if ingrediente_nombre in ingredientes_especial:
                            especiales_afectados.append({
                                'id': especial.id,
                                'nombre': especial.nombre,
                                'descripcion': especial.descripcion,
                                'precio': float(especial.precio) if especial.precio else 0.0,
                                'ingredientes': especial.ingredientes
                            })
                            print(f"   ✅ Especial afectado: {especial.nombre}")
                except Exception as e:
                    print(f"   ⚠️ Error procesando especial {especial.id}: {e}")
                    continue
            
            print(f"📊 Total especiales afectados: {len(especiales_afectados)}")
            
            # 2. Notificar a TODOS los administradores
            admins = User.query.filter_by(rol=1).all()
            notificaciones_admin = 0
            
            mensaje_admin = f"El ingrediente '{ingrediente.nombre}' ha sido marcado como INACTIVO.\n\n"
            
            if especiales_afectados:
                mensaje_admin += f"📋 ESPECIALES AFECTADOS ({len(especiales_afectados)}):\n"
                for i, especial in enumerate(especiales_afectados, 1):
                    mensaje_admin += f"{i}. {especial['nombre']} - ${especial['precio']:.2f}\n"
                    if especial['descripcion']:
                        desc = especial['descripcion'][:80] + "..." if len(especial['descripcion']) > 80 else especial['descripcion']
                        mensaje_admin += f"   Descripción: {desc}\n"
                    mensaje_admin += "\n"
            else:
                mensaje_admin += "📋 ESPECIALES AFECTADOS: 0\n"
                mensaje_admin += "No se encontraron especiales activos que contengan este ingrediente.\n\n"
            
            mensaje_admin += "⚠️ Los especiales afectados NO estarán disponibles para pedidos.\n"
            mensaje_admin += "📝 Acción sugerida: Revisar y actualizar los especiales afectados."
            
            for admin in admins:
                try:
                    notificacion = Notificacion.crear_notificacion_admin(
                        admin_id=admin.id,
                        tipo='ingrediente_inactivo',
                        titulo=f'🚨 INGREDIENTE INACTIVO: {ingrediente.nombre}',
                        mensaje=mensaje_admin,
                        datos_adicionales={
                            'ingrediente_id': ingrediente_id,
                            'ingrediente_nombre': ingrediente.nombre,
                            'especiales_afectados': especiales_afectados,
                            'total_especiales_afectados': len(especiales_afectados),
                            'accion': 'revisar_especiales',
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )
                    notificaciones_admin += 1
                    print(f"   ✅ Notificación admin creada: ID {notificacion.id}")
                    print(f"   👤 Admin ID: {admin.id}")
                    print(f"   📝 Tipo: ingrediente_inactivo")
                    print(f"   🏷️  User_type: admin")
                    
                except Exception as admin_error:
                    print(f"   ❌ Error notificando admin {admin.id}: {admin_error}")
            
            # 3. ¡¡¡IMPORTANTE!!! Notificar a TODOS los clientes (SIEMPRE)
            clientes = User.query.filter_by(rol=2).all()
            notificaciones_cliente = 0
            
            if len(clientes) > 0:
                print(f"\n👥 Enviando notificaciones a {len(clientes)} clientes...")
                
                # Mensaje para cliente
                mensaje_cliente = f"ACTUALIZACIÓN IMPORTANTE\n\n"
                mensaje_cliente += f"El ingrediente '{ingrediente.nombre}' ya no está disponible.\n\n"
                
                if especiales_afectados:
                    mensaje_cliente += "Esto afecta los siguientes especiales del día:\n"
                    for i, especial in enumerate(especiales_afectados[:3], 1):
                        mensaje_cliente += f"• {especial['nombre']}\n"
                    
                    if len(especiales_afectados) > 3:
                        mensaje_cliente += f"• ... y {len(especiales_afectados) - 3} más\n"
                    
                    mensaje_cliente += "\n⚠️ Estos especiales no estarán disponibles hasta nuevo aviso.\n"
                else:
                    mensaje_cliente += "⚠️ Esto podría afectar algunos de nuestros especiales.\n"
                
                mensaje_cliente += "\nGracias por tu comprensión.\n"
                mensaje_cliente += "\n📍 Restaurante: [Nombre del restaurante]"
                mensaje_cliente += "\n📞 Teléfono: [Número de teléfono]"
                
                for cliente in clientes:
                    try:
                        notificacion = Notificacion.crear_notificacion_cliente(
                            cliente_id=cliente.id,
                            tipo='ingrediente_inactivo',
                            titulo=f'⚠️ Actualización de Menú - {ingrediente.nombre}',
                            mensaje=mensaje_cliente,
                            datos_adicionales={
                                'ingrediente_id': ingrediente_id,
                                'ingrediente_nombre': ingrediente.nombre,
                                'especiales_afectados_count': len(especiales_afectados),
                                'accion': 'informacion',
                                'timestamp': datetime.utcnow().isoformat(),
                                'cliente_nombre': cliente.nombre,
                                'cliente_telefono': cliente.telefono
                            }
                        )
                        notificaciones_cliente += 1
                        
                        if notificaciones_cliente % 50 == 0:
                            print(f"   📨 Notificaciones enviadas a {notificaciones_cliente} clientes...")
                            
                    except Exception as cliente_error:
                        print(f"   ❌ Error notificando cliente {cliente.id}: {cliente_error}")
            else:
                print(f"   ⚠️ No hay clientes registrados para notificar")
            
            print(f"\n📈 RESUMEN FINAL:")
            print(f"   • Ingrediente: {ingrediente.nombre}")
            print(f"   • Estado: {'INACTIVO' if not ingrediente.activo else 'ACTIVO'}")
            print(f"   • Especiales afectados: {len(especiales_afectados)}")
            print(f"   • Admins notificados: {notificaciones_admin}")
            print(f"   • Clientes notificados: {notificaciones_cliente}")
            print(f"🔔 [NOTIFICACIONES] ========== FIN ==========\n")
            
            return True
            
        except Exception as error:
            print(f"❌ ERROR CRÍTICO en _enviar_notificaciones_desactivacion: {error}")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def get_by_categoria(cls, categoria, only_active=True):
        """Obtener ingredientes por categoría"""
        query = cls.query.filter_by(categoria=categoria)
        
        if only_active:
            query = query.filter_by(activo=True)
        
        return query.order_by(cls.nombre.asc()).all()
    
    @classmethod
    def get_categorias(cls):
        """Obtener lista de categorías únicas"""
        categorias = cls.query.with_entities(cls.categoria).distinct().all()
        return [cat[0] for cat in categorias if cat[0] is not None]
    
    @classmethod
    def search_ingredientes(cls, query):
        """Buscar ingredientes por nombre o categoría"""
        if query:
            return cls.query.filter(
                (cls.nombre.ilike(f'%{query}%')) | 
                (cls.categoria.ilike(f'%{query}%'))
            ).all()
        return cls.query.all()
    
    @classmethod
    def bulk_crear_ingredientes(cls, ingredientes_list):
        """Crear múltiples ingredientes a la vez"""
        creados = []
        for ingrediente_data in ingredientes_list:
            try:
                existente = cls.find_by_name(ingrediente_data['nombre'])
                if not existente:
                    ingrediente_id = cls.create_ingrediente(ingrediente_data)
                    creados.append(ingrediente_id)
            except Exception as e:
                print(f"Error al crear ingrediente {ingrediente_data['nombre']}: {e}")
        
        return creados
    
    @classmethod
    def to_dict(cls, ingrediente):
        """Convertir ingrediente a diccionario"""
        return {
            'id': ingrediente.id,
            'nombre': ingrediente.nombre,
            'categoria': ingrediente.categoria,
            'activo': ingrediente.activo,
            'fecha_creacion': ingrediente.fecha_creacion.isoformat() if ingrediente.fecha_creacion else None,
            'fecha_actualizacion': ingrediente.fecha_actualizacion.isoformat() if ingrediente.fecha_actualizacion else None
        }