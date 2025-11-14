import mysql.connector
from pymongo import MongoClient
import bcrypt
import os
from datetime import datetime
from dotenv import load_dotenv
import getpass 

load_dotenv()

class SistemaAutenticacion:
    
    def __init__(self):
        """Configura las conexiones a ambas bases de datos al iniciar."""
        self.mysql_cnx = None
        self.mongo_client = None
        self.mongo_db = None
        self.usuario_actual = None 

        try:
            # --- 1. Conectar a MySQL (con Puerto) ---
            self.mysql_config = {
                'host': os.getenv('MYSQL_HOST'),
                'user': os.getenv('MYSQL_USER'),
                'password': os.getenv('MYSQL_PASSWORD'),
                'database': os.getenv('MYSQL_DATABASE'),
                # --- !! AJUSTE IMPORTANTE !! ---
                'port': int(os.getenv('MYSQL_PORT')) # Añadimos el puerto y lo convertimos a entero
            }
            
            # Probamos la conexión MySQL
            self.mysql_cnx = mysql.connector.connect(**self.mysql_config)
            print("✅ Conexión a MySQL (Railway.app) exitosa.")
            
            # --- 2. Conectar a MongoDB ---
            self.mongo_uri = os.getenv('MONGO_URI')
            if not self.mongo_uri:
                raise ValueError("MONGO_URI no encontrada en .env")
                
            self.mongo_client = MongoClient(self.mongo_uri)
            
            # Usamos la base de datos que definimos antes
            self.mongo_db = self.mongo_client['examen_parcial_db'] 
            
            self.mongo_client.admin.command('ping')
            print(f"✅ Conexión a MongoDB (Atlas) exitosa. (Usando DB: {self.mongo_db.name})")

        except mysql.connector.Error as err:
            print(f"❌ Error fatal conectando a MySQL: {err}")
            exit()
        except Exception as e:
            print(f"❌ Error fatal conectando a MongoDB: {e}")
            exit()

    def hash_password(self, password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed

    def verificar_password(self, password, password_hash):
        try:
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            
            return bcrypt.checkpw(password.encode('utf-8'), password_hash)
        except ValueError:
            print("Error al verificar hash. ¿Formato incorrecto?")
            return False

    def registrar_usuario(self):
        print("\n--- 📝 Registro de Nuevo Usuario ---")
        username = input("Nombre de usuario: ")
        email = input("Email: ")
        password = getpass.getpass("Contraseña (no se verá): ")

        if not username or not email or not password:
            print("❌ Todos los campos son obligatorios.")
            return

        pwd_hash = self.hash_password(password)
        
        mysql_conn = None
        try:
            mysql_conn = mysql.connector.connect(**self.mysql_config)
            cursor = mysql_conn.cursor()
            
            query = """
            INSERT INTO usuarios (username, email, password_hash, activo) 
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (username, email, pwd_hash.decode('utf-8'), True))
            mysql_conn.commit()
            
            user_id_mysql = cursor.lastrowid
            
            doc_usuario = {
                "mysql_id": user_id_mysql, 
                "username": username,
                "email": email,
                "password_hash": pwd_hash.decode('utf-8'),
                "fecha_registro": datetime.now(),
                "activo": True,
                "rol": "usuario" 
            }
            self.mongo_db.usuarios.insert_one(doc_usuario)
            
            print(f"\n✨ ¡Usuario '{username}' registrado exitosamente en ambas BD!")

        except mysql.connector.Error as err:
            if err.errno == 1062: 
                print(f"❌ Error: El usuario o email '{username}' / '{email}' ya existe.")
            else:
                print(f"❌ Error MySQL al registrar: {err}")
        except Exception as e:
            print(f"❌ Error MongoDB al registrar: {e}")
        finally:
            if mysql_conn and mysql_conn.is_connected():
                cursor.close()
                mysql_conn.close()

    def registrar_log(self, usuario_id, accion, detalles=""):
        try:
            log_entry = {
                "usuario_id_mysql": usuario_id, 
                "accion": accion,
                "fecha": datetime.now(),
                "ip": "127.0.0.1", 
                "detalles": detalles
            }
            self.mongo_db.logs_actividad.insert_one(log_entry)
            print(f"📝 Log registrado: {accion}")
        except Exception as e:
            print(f"Advertencia: No se pudo registrar el log en MongoDB. {e}")

    def login(self):
        print("\n--- 🔒 Inicio de Sesión ---")
        email = input("Email: ")
        password = getpass.getpass("Contraseña: ")
        
        mysql_conn = None
        try:
            mysql_conn = mysql.connector.connect(**self.mysql_config)
            cursor = mysql_conn.cursor(dictionary=True) 
            
            cursor.execute("SELECT * FROM usuarios WHERE email = %s AND activo = TRUE", (email,))
            usuario = cursor.fetchone()
            
            if usuario and self.verificar_password(password, usuario['password_hash']):
                print(f"\n🔓 ¡Bienvenido, {usuario['username']}!")
                self.usuario_actual = usuario 
                
                self.registrar_log(usuario['id'], "login_exitoso")
                
                self.mostrar_menu_usuario()
            else:
                print("\n❌ Credenciales incorrectas o usuario inactivo.")
                self.registrar_log(0, "login_fallido", detalles=f"Intento con email: {email}")

        except mysql.connector.Error as err:
            print(f"❌ Error de BD durante el login: {err}")
        finally:
            if mysql_conn and mysql_conn.is_connected():
                cursor.close()
                mysql_conn.close()

    def mostrar_menu_usuario(self):
        if not self.usuario_actual:
            print("Error: No hay usuario en sesión.")
            return

        while True:
            print(f"\n--- 👤 Sesión de: {self.usuario_actual['username']} ---")
            print("1. Ver mi información (MySQL + Mongo)")
            print("2. Editar perfil (Simulado)")
            print("3. Cerrar Sesión")
            
            opcion = input("Selecciona una opción: ")
            
            if opcion == "1":
                self.mostrar_informacion_usuario()
            elif opcion == "2":
                self.editar_perfil_simulado()
            elif opcion == "3":
                self.cerrar_sesion()
                break 
            else:
                print("Opción no válida.")

    def mostrar_informacion_usuario(self):
        print("\n--- ℹ️ Tu Información ---")
        print(f"[MySQL] ID: {self.usuario_actual['id']}")
        print(f"[MySQL] Username: {self.usuario_actual['username']}")
        print(f"[MySQL] Email: {self.usuario_actual['email']}")
        print(f"[MySQL] Fecha Registro: {self.usuario_actual['fecha_registro']}")
        
        try:
            mongo_user = self.mongo_db.usuarios.find_one({"mysql_id": self.usuario_actual['id']})
            if mongo_user:
                print(f"[MongoDB] Rol: {mongo_user.get('rol', 'N/A')}")
            else:
                print("[MongoDB] No se encontró registro espejo.")
        except Exception as e:
            print(f"Error buscando datos en MongoDB: {e}")

    def editar_perfil_simulado(self):
        print("\n--- ✏️ Editar Perfil (Simulación) ---")
        print(f"Tu email actual es: {self.usuario_actual['email']}")
        nuevo_email = input("Ingresa nuevo email (deja vacío para cancelar): ")
        
        if nuevo_email:
            print(f"✅ (Simulado) Email actualizado a {nuevo_email}.")
            self.registrar_log(self.usuario_actual['id'], "edicion_perfil")
        else:
            print("Cancelado.")

    def cerrar_sesion(self):
        print(f"\n👋 Adiós, {self.usuario_actual['username']}. Sesión cerrada.")
        self.registrar_log(self.usuario_actual['id'], "logout")
        self.usuario_actual = None 

    def recuperacion_simulada(self):
        print("\n--- 🔑 Recuperación de Contraseña (Simulación) ---")
        email = input("Ingresa tu email para recuperar contraseña: ")
        if email:
            print(f"✅ (Simulado) Si el email {email} existe, se ha enviado un enlace.")
            self.registrar_log(0, "recuperacion_password", detalles=f"Intento para: {email}")
        else:
            print("Cancelado.")

    def main(self):
        while True:
            if self.usuario_actual:
                self.mostrar_menu_usuario()
            
            print("\n===== 🔐 SISTEMA DE AUTENTICACIÓN HÍBRIDO =====")
            print("1. Iniciar Sesión")
            print("2. Registrar Nuevo Usuario")
            print("3. Recuperar Contraseña (Simulado)")
            print("4. Salir")
            
            opcion = input("Selecciona una opción: ")
            
            if opcion == "1":
                self.login()
            elif opcion == "2":
                self.registrar_usuario()
            elif opcion == "3":
                self.recuperacion_simulada()
            elif opcion == "4":
                print("\nGracias por usar el sistema. ¡Hasta pronto!")
                if self.mysql_cnx and self.mysql_cnx.is_connected():
                    self.mysql_cnx.close()
                if self.mongo_client:
                    self.mongo_client.close()
                break 
            else:
                print("❌ Opción no válida, intenta de nuevo.")


if __name__ == "__main__":
    try:
        app = SistemaAutenticacion()
        app.main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"\nHa ocurrido un error inesperado: {e}")