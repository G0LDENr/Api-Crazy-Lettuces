SET FOREIGN_KEY_CHECKS=0;

-- Datos de la tabla: alembic_version
INSERT IGNORE INTO `alembic_version` (`version_num`) VALUES 
  ('9ba9ad5706f7');
-- Fin de datos para tabla: alembic_version

-- Datos de la tabla: backups
-- Tabla `backups` está vacía
-- Fin de datos para tabla: backups

-- Datos de la tabla: direcciones
REPLACE INTO `direcciones` (`id`, `user_id`, `calle`, `numero_exterior`, `numero_interior`, `colonia`, `ciudad`, `estado`, `codigo_postal`, `referencias`, `tipo`, `predeterminada`, `activa`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 1, 'LAS PALMAS', 'S/N', 'S/N', 'SANTA MARIA ATARASQUILLO', 'ATARASQUILLO', 'MEXICO', '52044', 'Entre calle ricardo flores magon y Antigua calle ', 'casa', 1, 1, '2026-02-16 20:36:24', '2026-02-16 20:36:24'),
  (2, 2, 'Av de las Palmas', '117', '', 'Santa Maria Atarasquillo', 'Santa María Atarasquillo', 'Méx.', '52050', '', 'casa', 1, 1, '2026-02-16 20:39:14', '2026-02-16 20:39:14'),
  (3, 3, 'Av de las Palmas', '117', '', 'Santa Maria Atarasquillo', 'Santa María Atarasquillo', 'Méx.', '52050', '', 'casa', 1, 1, '2026-02-16 20:50:44', '2026-02-16 20:50:44');
-- Fin de datos para tabla: direcciones

-- Datos de la tabla: especiales
REPLACE INTO `especiales` (`id`, `nombre`, `ingredientes`, `precio`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Mediterráneo Cremoso', 'Pollo, Queso Mozzarella, Tomate, Crema, Aceite de olivo, Limon, Sal', '70.00', 1, '2026-02-16 20:57:51', '2026-02-16 20:57:51'),
  (2, 'Cítrico Delight', 'Pollo, Limon, Aceite de olivo, Sal', '30.00', 1, '2026-02-16 20:59:18', '2026-02-16 20:59:18'),
  (3, 'Tomate Aromático', 'Tomate, Aceite de olivo, Sal, Limon', '35.00', 1, '2026-02-16 21:00:06', '2026-02-16 21:00:06');
-- Fin de datos para tabla: especiales

-- Datos de la tabla: ingredientes
REPLACE INTO `ingredientes` (`id`, `nombre`, `categoria`, `activo`, `fecha_creacion`, `fecha_actualizacion`) VALUES 
  (1, 'Tomate', 'vegetales', 1, '2026-02-16 20:45:10', '2026-02-16 20:45:10'),
  (2, 'Pollo', 'proteinas', 1, '2026-02-16 20:45:10', '2026-02-16 20:48:36'),
  (3, 'Crema', 'lacteos', 1, '2026-02-16 20:49:31', '2026-02-16 20:49:31'),
  (4, 'Sal', 'condimentos', 1, '2026-02-16 20:52:14', '2026-02-16 20:52:14'),
  (5, 'Queso Mozzarella', 'lacteos', 1, '2026-02-16 20:52:47', '2026-02-16 20:53:40'),
  (6, 'Limon', 'vegetales', 1, '2026-02-16 20:52:57', '2026-02-16 20:52:57'),
  (7, 'Aceite de olivo', 'condimentos', 1, '2026-02-16 20:54:19', '2026-02-16 20:54:19');
-- Fin de datos para tabla: ingredientes

-- Datos de la tabla: notificaciones
-- Tabla `notificaciones` está vacía
-- Fin de datos para tabla: notificaciones

-- Datos de la tabla: ordenes
-- Tabla `ordenes` está vacía
-- Fin de datos para tabla: ordenes

-- Datos de la tabla: users
REPLACE INTO `users` (`id`, `nombre`, `correo`, `contraseña`, `rol`, `telefono`, `sexo`, `fecha_registro`) VALUES 
  (1, 'Juan Carlos Villavicencio Gonzalez', 'carlos.villavicenciog180@gmail.com', '$2b$12$KZB7xy/os7MK7Y3SUaosW.vmODxqeGHc2kO2RixhQse993nDJUlrG', 1, '7294030702', 'Masculino', '2026-02-16 20:36:24'),
  (2, 'Amanda Carolina Jimenez Ocampo', 'amanda@gmail.com', '$2b$12$w8pNaNXpqUF5lf6SjPhmweSLWwAMxc3lU6wwPee8c9LvY2iJQ7wpq', 1, '7228984632', 'Femenino', '2026-02-16 20:39:14'),
  (3, 'Azalia Mejia', 'azalia@gmail.com', '$2b$12$xixjx307EKTlv8m65vDePe/qTAXYn85OkpRzo1wRdHMn1lBRtaPVC', 2, '7228963187', 'Femenino', '2026-02-16 20:50:44');
-- Fin de datos para tabla: users

SET FOREIGN_KEY_CHECKS=1;
SET FOREIGN_KEY_CHECKS=1;
