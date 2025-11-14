# Examen Práctico: Sistema de Autenticación Híbrido

> **Nota Importante para el Profesor:**
> Para facilitar las pruebas y la evaluación directa de este proyecto, el archivo `.env` con las credenciales de conexión ha sido incluido en el repositorio. Entendemos que en un entorno profesional, este archivo **nunca** debe ser público y siempre debe ser ignorado (`.gitignore`). Esto se ha hecho únicamente con fines académicos y de evaluación.

## 1. Instrucciones de Instalación y Ejecución

1.  Clonar este repositorio:
    ```bash
    git clone <tu-url-de-github>
    cd <nombre-del-repositorio>
    ```

2.  Crear y activar un entorno virtual:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  Instalar las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Importante:** Abrir el archivo `.env` y asegurarse de que la contraseña de MongoDB (`MONGO_URI`) sea la correcta.

5.  Ejecutar la aplicación:
    ```bash
    python main.py
    ```

## 2. Estructura de la Base de Datos

### MySQL (Railway)
```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);