SET FOREIGN_KEY_CHECKS=0;

-- Datos de la tabla: alembic_version
INSERT IGNORE INTO `alembic_version` (`version_num`) VALUES 
  ('d3698f8e703c');
-- Fin de datos para tabla: alembic_version

-- Datos de la tabla: backups
-- Tabla `backups` está vacía
-- Fin de datos para tabla: backups

-- Datos de la tabla: direcciones
REPLACE INTO `direcciones` (`id`, `user_id`, `calle`, `numero_exterior`, `numero_interior`, `colonia`, `ciudad`, `estado`, `codigo_postal`, `referencias`, `tipo`, `predeterminada`, `activa`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 1, 'Av. Principal', '123', NULL, 'Centro', 'CDMX', 'Ciudad de México', '01000', 'Entre calles', 'casa', 1, 1, '2026-02-12 18:49:27', '2026-02-12 18:49:27'),
  (5, 5, 'Calle de las Palmas', 'S/N', 'S/N', 'Atarasquillo', 'CDMX', 'Mexico', '52044', '', 'casa', 1, 1, '2026-02-12 23:33:11', '2026-02-12 23:33:11'),
  (6, 6, 'Calle de las Palmas', 'S/N', NULL, 'Atarasquillo', 'CDMX', 'Lerma', '52044', 'Entre calles', 'casa', 1, 1, '2026-02-12 23:39:36', '2026-02-12 23:39:36');
-- Fin de datos para tabla: direcciones

-- Datos de la tabla: especiales
REPLACE INTO `especiales` (`id`, `nombre`, `ingredientes`, `precio`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Picosito', 'Chamoy, Chile en Polvo, Limon', '40.00', 1, '2026-02-12 18:54:29', '2026-02-12 18:54:29');
-- Fin de datos para tabla: especiales

-- Datos de la tabla: ingredientes
REPLACE INTO `ingredientes` (`id`, `nombre`, `categoria`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Chile en Polvo', 'condimentos', 1, '2026-02-12 18:53:24', '2026-02-12 18:53:24'),
  (2, 'Limon', 'vegetales', 1, '2026-02-12 18:53:45', '2026-02-12 18:53:45'),
  (3, 'Chamoy', 'aderezos', 1, '2026-02-12 18:54:00', '2026-02-12 18:54:00');
-- Fin de datos para tabla: ingredientes

-- Datos de la tabla: notificaciones
REPLACE INTO `notificaciones` (`id`, `user_id`, `user_type`, `tipo`, `titulo`, `mensaje`, `leida`, `datos_adicionales`, `fecha_creacion`, `fecha_leida`, `orden_id`) VALUES 
  (1, 1, 'admin', 'nuevo_pedido', 'Pedido #I2R1LQ', 'NUEVO PEDIDO #I2R1LQ
Cliente: Juan Manuel
Tel: 5555897631
Pedido: Picosito
Método pago: Pago en efectivo
Total: $40.00', 0, '{"notas": null, "estado": "pendiente", "precio": 40.0, "orden_id": 1, "info_pago": null, "timestamp": "2026-02-12T18:56:36.290832", "metodo_pago": "efectivo", "tipo_pedido": "especial", "fecha_pedido": "2026-02-12T18:56:36", "codigo_pedido": "I2R1LQ", "cliente_nombre": "Juan Manuel", "producto_nombre": "Picosito", "telefono_cliente": "5555897631", "detalles_completos": "Picosito", "direccion_completa": "Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044", "ingredientes_completos": null}', '2026-02-12 18:56:36', NULL, 1),
  (2, 2, 'cliente', 'confirmacion_pedido', 'Pedido recibido #I2R1LQ', 'Tu pedido #I2R1LQ ha sido recibido.
Total: $40.00
Método pago: Pago en efectivo
Te notificaremos cuando esté en proceso.', 0, '{"notas": null, "estado": "pendiente", "precio": 40.0, "orden_id": 1, "info_pago": null, "timestamp": "2026-02-12T18:56:36.290832", "metodo_pago": "efectivo", "tipo_pedido": "especial", "fecha_pedido": "2026-02-12T18:56:36", "codigo_pedido": "I2R1LQ", "cliente_nombre": "Juan Manuel", "producto_nombre": "Picosito", "telefono_cliente": "5555897631", "detalles_completos": "Picosito", "direccion_completa": "Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044", "ingredientes_completos": null}', '2026-02-12 18:56:36', NULL, 1),
  (3, 1, 'admin', 'nuevo_pedido', 'Pedido #1H01OI', 'NUEVO PEDIDO #1H01OI
Cliente: Juan Manuel
Tel: 5555897631
Pedido: Picosito
Método pago: 💳 Pago con tarjeta (****9843)
Total: $40.00', 0, '{"notas": null, "estado": "pendiente", "precio": 40.0, "orden_id": 2, "info_pago": "{\"tipo\": \"visa\", \"ultimos_4\": \"9843\", \"titular\": \"Juan Manuel\"}", "timestamp": "2026-02-12T22:47:57.861938", "metodo_pago": "tarjeta", "tipo_pedido": "especial", "fecha_pedido": "2026-02-12T22:47:58", "codigo_pedido": "1H01OI", "cliente_nombre": "Juan Manuel", "producto_nombre": "Picosito", "telefono_cliente": "5555897631", "detalles_completos": "Picosito", "direccion_completa": "Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044", "ingredientes_completos": null}', '2026-02-12 22:47:58', NULL, 2),
  (4, 3, 'admin', 'nuevo_pedido', 'Pedido #1H01OI', 'NUEVO PEDIDO #1H01OI
Cliente: Juan Manuel
Tel: 5555897631
Pedido: Picosito
Método pago: 💳 Pago con tarjeta (****9843)
Total: $40.00', 0, '{"notas": null, "estado": "pendiente", "precio": 40.0, "orden_id": 2, "info_pago": "{\"tipo\": \"visa\", \"ultimos_4\": \"9843\", \"titular\": \"Juan Manuel\"}", "timestamp": "2026-02-12T22:47:57.861938", "metodo_pago": "tarjeta", "tipo_pedido": "especial", "fecha_pedido": "2026-02-12T22:47:58", "codigo_pedido": "1H01OI", "cliente_nombre": "Juan Manuel", "producto_nombre": "Picosito", "telefono_cliente": "5555897631", "detalles_completos": "Picosito", "direccion_completa": "Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044", "ingredientes_completos": null}', '2026-02-12 22:47:58', NULL, 2),
  (5, 2, 'cliente', 'confirmacion_pedido', 'Pedido recibido #1H01OI', 'Tu pedido #1H01OI ha sido recibido.
Total: $40.00
Método pago: 💳 Pago con tarjeta (****9843)
Te notificaremos cuando esté en proceso.', 0, '{"notas": null, "estado": "pendiente", "precio": 40.0, "orden_id": 2, "info_pago": "{\"tipo\": \"visa\", \"ultimos_4\": \"9843\", \"titular\": \"Juan Manuel\"}", "timestamp": "2026-02-12T22:47:57.861938", "metodo_pago": "tarjeta", "tipo_pedido": "especial", "fecha_pedido": "2026-02-12T22:47:58", "codigo_pedido": "1H01OI", "cliente_nombre": "Juan Manuel", "producto_nombre": "Picosito", "telefono_cliente": "5555897631", "detalles_completos": "Picosito", "direccion_completa": "Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044", "ingredientes_completos": null}', '2026-02-12 22:47:58', NULL, 2);
-- Fin de datos para tabla: notificaciones

-- Datos de la tabla: ordenes
REPLACE INTO `ordenes` (`id`, `codigo_unico`, `nombre_usuario`, `telefono_usuario`, `tipo_pedido`, `especial_id`, `direccion_texto`, `direccion_id`, `ingredientes_personalizados`, `precio`, `metodo_pago`, `info_pago_json`, `notas`, `pedido_json`, `estado`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'I2R1LQ', 'Juan Manuel', '5555897631', 'especial', 1, 'Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044', NULL, NULL, '40.00', 'efectivo', NULL, NULL, '{"tipo":"especial","producto_nombre":"Picosito","cantidad":1,"precio_unitario":40,"total":40,"especial_id":1,"metodo_pago":"efectivo","fecha_pedido":"2026-02-12T18:56:36.238Z","items":[{"nombre":"Picosito","cantidad":1,"precio_unitario":40,"subtotal":40,"tipo":"especial"}],"direccion_entrega":"Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044","cliente_nombre":"Juan Manuel","cliente_telefono":"5555897631"}', 'pendiente', '2026-02-12 18:56:36', '2026-02-12 22:49:24'),
  (2, '1H01OI', 'Juan Manuel', '5555897631', 'especial', 1, 'Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044', NULL, NULL, '40.00', 'tarjeta', '{"tipo": "visa", "ultimos_4": "9843", "titular": "Juan Manuel"}', NULL, '{"tipo":"especial","producto_nombre":"Picosito","cantidad":1,"precio_unitario":40,"total":40,"especial_id":1,"metodo_pago":"tarjeta","fecha_pedido":"2026-02-12T22:47:57.797Z","items":[{"nombre":"Picosito","cantidad":1,"precio_unitario":40,"subtotal":40,"tipo":"especial"}],"direccion_entrega":"Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044","cliente_nombre":"Juan Manuel","cliente_telefono":"5555897631"}', 'pendiente', '2026-02-12 22:47:58', '2026-02-12 22:49:24');
-- Fin de datos para tabla: ordenes

-- Datos de la tabla: users
REPLACE INTO `users` (`id`, `nombre`, `correo`, `contraseña`, `rol`, `telefono`, `sexo`, `fecha_registro`) VALUES 
  (1, 'Juan Carlos', 'carlos@gmail.com', '$2b$12$Quj8lWn.L.ZCkiQIs8E1vesbcS7s5lRmocd25IgGf83trH9FJfQgi', 1, '7294030702', 'M', '2026-02-12 18:49:27'),
  (6, 'Amanda', 'amanda@gmail.com', '$2b$12$8n959TTWN8dVT8Dio29xGeZhGcAGBb638/mj72QyrU9lu8PKTpM0u', 1, '7294863520', 'F', '2026-02-12 23:39:36');
-- Fin de datos para tabla: users

SET FOREIGN_KEY_CHECKS=1;
SET FOREIGN_KEY_CHECKS=1;
