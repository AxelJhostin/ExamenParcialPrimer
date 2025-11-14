// 1. Comando para crear la colección de usuarios (opcional, se crea al insertar)
db.createCollection("usuarios")

// 2. Comando para crear un índice (¡Importante!)
// Esto hace que la búsqueda por 'email' o 'mysql_id' sea súper rápida
db.usuarios.createIndex({ "email": 1 }, { unique: true })
db.usuarios.createIndex({ "mysql_id": 1 })

// 3. Comando para crear la colección de logs (opcional, se crea al insertar)
db.createCollection("logs_actividad")

// 4. Comando para crear un índice en los logs
db.logs_actividad.createIndex({ "usuario_id_mysql": 1 })
db.logs_actividad.createIndex({ "fecha": -1 })