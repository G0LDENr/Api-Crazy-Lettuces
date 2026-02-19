-- Backup generado el 2026-02-12 17:10:49
-- Tipo: FULL
-- Tablas: 8
SET FOREIGN_KEY_CHECKS=0;

-- Estructura de la tabla: alembic_version
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: alembic_version
REPLACE INTO `alembic_version` (`version_num`) VALUES 
  ('d3698f8e703c');
-- Fin de datos para tabla: alembic_version

-- Estructura de la tabla: backups
CREATE TABLE `backups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `filepath` varchar(500) NOT NULL,
  `size_mb` float DEFAULT NULL,
  `tables_included` text,
  `backup_type` varchar(50) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: backups
-- Tabla `backups` está vacía
-- Fin de datos para tabla: backups

-- Estructura de la tabla: direcciones
CREATE TABLE `direcciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `calle` varchar(200) NOT NULL,
  `numero_exterior` varchar(20) NOT NULL,
  `numero_interior` varchar(20) DEFAULT NULL,
  `colonia` varchar(100) NOT NULL,
  `ciudad` varchar(100) NOT NULL,
  `estado` varchar(50) NOT NULL,
  `codigo_postal` varchar(10) NOT NULL,
  `referencias` text,
  `tipo` varchar(20) DEFAULT NULL,
  `predeterminada` tinyint(1) DEFAULT NULL,
  `activa` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `direcciones_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: direcciones
REPLACE INTO `direcciones` (`id`, `user_id`, `calle`, `numero_exterior`, `numero_interior`, `colonia`, `ciudad`, `estado`, `codigo_postal`, `referencias`, `tipo`, `predeterminada`, `activa`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 1, 'Av. Principal', '123', NULL, 'Centro', 'CDMX', 'Ciudad de México', '01000', 'Entre calles', 'casa', 1, 1, '2026-02-12 18:49:27', '2026-02-12 18:49:27'),
  (4, 4, 'Calle de las Palmas', 'S/N', NULL, 'Atarasquillo', 'CDMX', 'Lerma', '52044', 'Entre calles', 'casa', 1, 1, '2026-02-12 23:10:26', '2026-02-12 23:10:26');
-- Fin de datos para tabla: direcciones

-- Estructura de la tabla: especiales
CREATE TABLE `especiales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `ingredientes` text NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: especiales
REPLACE INTO `especiales` (`id`, `nombre`, `ingredientes`, `precio`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Picosito', 'Chamoy, Chile en Polvo, Limon', '40.00', 1, '2026-02-12 18:54:29', '2026-02-12 18:54:29');
-- Fin de datos para tabla: especiales

-- Estructura de la tabla: ingredientes
CREATE TABLE `ingredientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: ingredientes
REPLACE INTO `ingredientes` (`id`, `nombre`, `categoria`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Chile en Polvo', 'condimentos', 1, '2026-02-12 18:53:24', '2026-02-12 18:53:24'),
  (2, 'Limon', 'vegetales', 1, '2026-02-12 18:53:45', '2026-02-12 18:53:45'),
  (3, 'Chamoy', 'aderezos', 1, '2026-02-12 18:54:00', '2026-02-12 18:54:00');
-- Fin de datos para tabla: ingredientes

-- Estructura de la tabla: notificaciones
CREATE TABLE `notificaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `user_type` varchar(20) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `titulo` varchar(200) NOT NULL,
  `mensaje` text NOT NULL,
  `leida` tinyint(1) DEFAULT NULL,
  `datos_adicionales` json DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_leida` datetime DEFAULT NULL,
  `orden_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `orden_id` (`orden_id`),
  CONSTRAINT `notificaciones_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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

-- Estructura de la tabla: ordenes
CREATE TABLE `ordenes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_unico` varchar(10) NOT NULL,
  `nombre_usuario` varchar(100) NOT NULL,
  `telefono_usuario` varchar(20) NOT NULL,
  `tipo_pedido` varchar(20) NOT NULL,
  `especial_id` int DEFAULT NULL,
  `direccion_texto` text,
  `direccion_id` int DEFAULT NULL,
  `ingredientes_personalizados` text,
  `precio` decimal(10,2) NOT NULL,
  `metodo_pago` varchar(20) DEFAULT NULL,
  `info_pago_json` text,
  `notas` text,
  `pedido_json` text,
  `estado` varchar(20) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  `fecha_actualizacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo_unico` (`codigo_unico`),
  KEY `direccion_id` (`direccion_id`),
  KEY `especial_id` (`especial_id`),
  CONSTRAINT `ordenes_ibfk_1` FOREIGN KEY (`direccion_id`) REFERENCES `direcciones` (`id`),
  CONSTRAINT `ordenes_ibfk_2` FOREIGN KEY (`especial_id`) REFERENCES `especiales` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: ordenes
REPLACE INTO `ordenes` (`id`, `codigo_unico`, `nombre_usuario`, `telefono_usuario`, `tipo_pedido`, `especial_id`, `direccion_texto`, `direccion_id`, `ingredientes_personalizados`, `precio`, `metodo_pago`, `info_pago_json`, `notas`, `pedido_json`, `estado`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'I2R1LQ', 'Juan Manuel', '5555897631', 'especial', 1, 'Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044', NULL, NULL, '40.00', 'efectivo', NULL, NULL, '{"tipo":"especial","producto_nombre":"Picosito","cantidad":1,"precio_unitario":40,"total":40,"especial_id":1,"metodo_pago":"efectivo","fecha_pedido":"2026-02-12T18:56:36.238Z","items":[{"nombre":"Picosito","cantidad":1,"precio_unitario":40,"subtotal":40,"tipo":"especial"}],"direccion_entrega":"Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044","cliente_nombre":"Juan Manuel","cliente_telefono":"5555897631"}', 'pendiente', '2026-02-12 18:56:36', '2026-02-12 22:49:24'),
  (2, '1H01OI', 'Juan Manuel', '5555897631', 'especial', 1, 'Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044', NULL, NULL, '40.00', 'tarjeta', '{"tipo": "visa", "ultimos_4": "9843", "titular": "Juan Manuel"}', NULL, '{"tipo":"especial","producto_nombre":"Picosito","cantidad":1,"precio_unitario":40,"total":40,"especial_id":1,"metodo_pago":"tarjeta","fecha_pedido":"2026-02-12T22:47:57.797Z","items":[{"nombre":"Picosito","cantidad":1,"precio_unitario":40,"subtotal":40,"tipo":"especial"}],"direccion_entrega":"Calle de las Palmas #S/N Int. S/N, Atarasquillo, CDMX, Mexico, CP: 52044","cliente_nombre":"Juan Manuel","cliente_telefono":"5555897631"}', 'pendiente', '2026-02-12 22:47:58', '2026-02-12 22:49:24');
-- Fin de datos para tabla: ordenes

-- Estructura de la tabla: users
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` int DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `sexo` varchar(10) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Datos de la tabla: users
REPLACE INTO `users` (`id`, `nombre`, `correo`, `password`, `rol`, `telefono`, `sexo`, `fecha_registro`) VALUES 
  (1, 'Juan Carlos', 'carlos@gmail.com', '$2b$12$Quj8lWn.L.ZCkiQIs8E1vesbcS7s5lRmocd25IgGf83trH9FJfQgi', 1, '7294030702', 'M', '2026-02-12 18:49:27'),
  (4, 'Amanda', 'amanda@gmail.com', '$2b$12$6tie7flVoHvcBmROoQTuUuSbbX1PV9ky5xVv.okRHgNrgrXF5RgH.', 1, '7294863520', 'F', '2026-02-12 23:10:26');
-- Fin de datos para tabla: users

SET FOREIGN_KEY_CHECKS=1;
-- Backup completado el 2026-02-12 17:10:49
