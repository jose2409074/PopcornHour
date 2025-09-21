from flask import Flask, render_template, request, redirect, url_for, session, abort
import psycopg2
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Mi contraseña de DB_PAAS debe estar en un archivo .env en la raíz del proyecto
# SECRET_KEY también debe estar en el archivo .env
# Por seguridad al compartirlo en GitHub
# El archivo .env debe tener el siguiente formato:
# SECRET_KEY=tu_clave_secreta
# DB_PASS=tu_contraseña_de_base_de_datos
DB_NAME = "popcornhour"
DB_USER = "postgres"
DB_PASS = os.getenv("DB_PASS")
DB_HOST = "localhost"

def get_db_connection():
    """Función para obtener una conexión a la base de datos."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST
    )
    return conn

# --- Rutas de la aplicación con las ventanas solicitadas---

@app.route('/')
def index():
    """Página de inicio para usuarios sin sesión."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_pelicula, titulo, sinopsis, url_portada FROM Peliculas")
    peliculas = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('index.html', peliculas=peliculas)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Procesa el inicio de sesión."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id_usuario, nombre, contraseña_hash, tipo_usuario FROM Usuarios WHERE email = %s", (email,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()

        if user_data:
            user_id, user_name, stored_hash_hex, user_type = user_data
            stored_hash_bytes = bytes.fromhex(stored_hash_hex)
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                # Determina el tipo de usuario basado en el correo, para simplificar el ejercicio.
                # Todos los correcos con terminación @admin.com serán moderadores
                user_type_from_email = 'moderador' if email.endswith('@admin.com') else user_type
                
                # Guarda la información necesaria del usuario en la sesión
                session['user_id'] = user_id
                session['user_email'] = email
                session['user_name'] = user_name
                session['user_type'] = user_type_from_email
                
                if user_type_from_email == 'moderador':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
        
        return "Contraseña o usuario incorrectos. <a href='/login'>Volver a intentar</a>"
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Procesa el registro de nuevos usuarios."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            return "Las contraseñas no coinciden. <a href='/signup'>Volver a intentar</a>"
        
        hashed_password_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_hex = hashed_password_bytes.hex()

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Usuarios (nombre, email, contraseña_hash, tipo_usuario) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password_hex, 'estandar') # El rol se asigna dinámicamente al logearse
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error al registrar: {e}. <a href='/signup'>Volver a intentar</a>"

    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Página de inicio para usuarios con sesión."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_pelicula, titulo, sinopsis, url_portada FROM Peliculas")
    peliculas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', peliculas=peliculas, user_name=session['user_name'])

@app.route('/admin')
def admin_dashboard():
    """Página de administración para moderadores. Lista las películas y usuarios."""
    if 'user_type' not in session or session.get('user_type') != 'moderador':
        abort(403)
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Consulta corregida para obtener la URL de la portada
    cur.execute("SELECT id_pelicula, titulo, url_portada FROM Peliculas ORDER BY titulo")
    peliculas = cur.fetchall()
    cur.execute("SELECT id_usuario, nombre, email, tipo_usuario FROM Usuarios ORDER BY nombre")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('admin.html', peliculas=peliculas, usuarios=usuarios)

@app.route('/admin/promote/<int:user_id>', methods=['POST'])
def promote_user(user_id):
    """Otorga privilegios de administrador a un usuario."""
    if session.get('user_type') != 'moderador':
        abort(403)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Usuarios SET tipo_usuario = 'moderador' WHERE id_usuario = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/demote/<int:user_id>', methods=['POST'])
def demote_user(user_id):
    """Revoca privilegios de administrador a un usuario."""
    if session.get('user_type') != 'moderador':
        abort(403)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Usuarios SET tipo_usuario = 'estandar' WHERE id_usuario = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Elimina un usuario de la base de datos."""
    # Evita que un administrador se elimine a sí mismo
    if session.get('user_type') != 'moderador' or session.get('user_id') == user_id:
        abort(403)

    # Por la constructión de la base de datos, primero se deben eliminar las calificaciones y comentarios asociados al usuario
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Eliminar calificaciones asociadas al usuario
        cur.execute("DELETE FROM Calificaciones WHERE id_usuario = %s", (user_id,))
        
        # 2. Eliminar comentarios asociados al usuario
        cur.execute("DELETE FROM Comentarios WHERE id_usuario = %s", (user_id,))
        
        # 3. Eliminar al usuario de la tabla principal
        cur.execute("DELETE FROM Usuarios WHERE id_usuario = %s", (user_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Error al eliminar usuario: {e}. <a href='/admin'>Volver</a>"
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    """Procesa la subida de una película por un moderador."""
    if session.get('user_type') != 'moderador':
        abort(403)

    if request.method == 'POST':
        titulo = request.form['titulo']
        sinopsis = request.form['sinopsis']
        ano = request.form['ano']
        duracion = request.form['duracion']
        genero = request.form['genero']
        url_portada = request.form['url_portada']

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Peliculas (titulo, sinopsis, año, duracion_min, genero, url_portada) VALUES (%s, %s, %s, %s, %s, %s)",
                (titulo, sinopsis, ano, duracion, genero, url_portada)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            return f"Error al subir película: {e}. <a href='/add_movie'>Volver a intentar</a>"
    
    return render_template('add_movie.html')

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    """Muestra los detalles de una película específica."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT titulo, sinopsis, url_portada, año, duracion_min, genero FROM Peliculas WHERE id_pelicula = %s", (movie_id,))
    pelicula = cur.fetchone()

    cur.execute("SELECT texto FROM Comentarios WHERE id_pelicula = %s", (movie_id,))
    comentarios = cur.fetchall()

    cur.execute("SELECT AVG(puntuacion) FROM Calificaciones WHERE id_pelicula = %s", (movie_id,))
    promedio_calificacion = cur.fetchone()[0]

    cur.close()
    conn.close()

    if pelicula is None:
        abort(404)

    return render_template('movie_details.html', pelicula=pelicula, comentarios=comentarios, promedio_calificacion=promedio_calificacion, movie_id=movie_id)

@app.route('/rate/<int:movie_id>', methods=['POST'])
def rate_movie(movie_id):
    """Procesa la calificación de una película."""
    if 'user_id' not in session:
        return "Debes iniciar sesión para calificar. <a href='/login'>Iniciar Sesión</a>"
    
    puntuacion = request.form['puntuacion']
    user_id = session.get('user_id')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Calificaciones (puntuacion, id_usuario, id_pelicula) VALUES (%s, %s, %s)", (puntuacion, user_id, movie_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('movie_details', movie_id=movie_id))
    except Exception as e:
        return f"Error al calificar: {e}. <a href='/movie/{movie_id}'>Volver</a>"

@app.route('/comment/<int:movie_id>', methods=['POST'])
def comment_movie(movie_id):
    """Procesa el comentario de una película."""
    if 'user_id' not in session:
        return "Debes iniciar sesión para comentar. <a href='/login'>Iniciar Sesión</a>"
    
    texto = request.form['comentario']
    user_id = session.get('user_id')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Comentarios (texto, id_usuario, id_pelicula) VALUES (%s, %s, %s)", (texto, user_id, movie_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('movie_details', movie_id=movie_id))
    except Exception as e:
        return f"Error al comentar: {e}. <a href='/movie/{movie_id}'>Volver</a>"

@app.route('/admin/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    """Ruta para editar una película existente."""
    if session.get('user_type') != 'moderador':
        abort(403)

    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        # Procesar los datos del formulario de edición
        titulo = request.form['titulo']
        sinopsis = request.form['sinopsis']
        ano = request.form['ano']
        duracion = request.form['duracion']
        genero = request.form['genero']
        url_portada = request.form['url_portada']
        
        cur.execute("""
            UPDATE Peliculas 
            SET titulo=%s, sinopsis=%s, año=%s, duracion_min=%s, genero=%s, url_portada=%s
            WHERE id_pelicula=%s
        """, (titulo, sinopsis, ano, duracion, genero, url_portada, movie_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    # Mostrar el formulario de edición
    cur.execute("SELECT titulo, sinopsis, año, duracion_min, genero, url_portada FROM Peliculas WHERE id_pelicula = %s", (movie_id,))
    pelicula = cur.fetchone()
    conn.close()
    
    if pelicula is None:
        abort(404)
        
    return render_template('edit_movie.html', pelicula=pelicula, movie_id=movie_id)


@app.route('/admin/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    """Ruta para eliminar una película."""
    if session.get('user_type') != 'moderador':
        abort(403)
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Peliculas WHERE id_pelicula = %s", (movie_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

