# PopcornHour: Portal de Películas y Series
PopcornHour es un portal web interactivo donde los usuarios pueden calificar, comentar y descubrir nuevas películas y series. La plataforma cuenta con dos tipos de usuarios:

Estándar: Puede navegar por el catálogo, calificar películas y dejar comentarios.

Moderador: Accede a un panel de administración para añadir, editar y eliminar películas, así como gestionar a otros usuarios. El acceso de moderador se otorga automáticamente a los usuarios que se registran con un email que termine en @admin.com.

## Se desarrolló usando python 3.12.10 y PostgreSQL.

## Configuración
Base de Datos: Se agregó el script SQL en la carpeta documentation/db/create_tables.sql, junto al esquema de entidad-relación para simplificar el proceso de crear la base de datos popcornhour y todas sus tablas.

### Para conservar las contraseñas seguras se añadieron a un archivo local restringido por .gitignore, por lo que para replicarlo es necesario crear el archivo que se menciona a continuación con tus propias contraseñas.

Variables de Entorno: Crea un archivo .env en la raíz del proyecto. Este archivo debe contener tus credenciales de PostgreSQL y una clave secreta para la aplicación, por ejemplo:

DB_PASS="<tu_contraseña_de_postgresql>"
SECRET_KEY="<una_clave_secreta_larga_y_aleatoria>"

## ¿Cómo ejecutar el proyecto?
Una vez que hayas completado la configuración, puedes iniciar la aplicación.

python app.py

#### La aplicación estará disponible en tu navegador en la dirección http://127.0.0.1:5000/.