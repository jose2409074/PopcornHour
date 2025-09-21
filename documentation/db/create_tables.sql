-- Tabla para los usuarios
CREATE TABLE IF NOT EXISTS public.usuarios
(
    id_usuario integer NOT NULL DEFAULT nextval('usuarios_id_usuario_seq'::regclass),
    nombre character varying(100) COLLATE pg_catalog."default" NOT NULL,
    email character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "contraseña_hash" character varying(255) COLLATE pg_catalog."default" NOT NULL,
    tipo_usuario character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT usuarios_pkey PRIMARY KEY (id_usuario),
    CONSTRAINT usuarios_email_key UNIQUE (email),
    CONSTRAINT usuarios_tipo_usuario_check CHECK (tipo_usuario::text = ANY (ARRAY['estandar'::character varying, 'moderador'::character varying]::text[]))
);

-- Tabla para las películas
CREATE TABLE IF NOT EXISTS public.peliculas
(
    id_pelicula integer NOT NULL DEFAULT nextval('peliculas_id_pelicula_seq'::regclass),
    titulo character varying(255) COLLATE pg_catalog."default" NOT NULL,
    sinopsis text COLLATE pg_catalog."default",
    año integer,
    duracion_min integer,
    genero character varying(100) COLLATE pg_catalog."default",
    url_portada character varying(255) COLLATE pg_catalog."default",
    CONSTRAINT peliculas_pkey PRIMARY KEY (id_pelicula)
);

-- Tabla para las calificaciones
CREATE TABLE IF NOT EXISTS public.calificaciones
(
    id_calificacion integer NOT NULL DEFAULT nextval('calificaciones_id_calificacion_seq'::regclass),
    puntuacion integer,
    id_usuario integer NOT NULL,
    id_pelicula integer NOT NULL,
    CONSTRAINT calificaciones_pkey PRIMARY KEY (id_calificacion),
    CONSTRAINT calificaciones_id_pelicula_fkey FOREIGN KEY (id_pelicula)
        REFERENCES public.peliculas (id_pelicula) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT calificaciones_id_usuario_fkey FOREIGN KEY (id_usuario)
        REFERENCES public.usuarios (id_usuario) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT calificaciones_puntuacion_check CHECK (puntuacion >= 1 AND puntuacion <= 5)
);

-- Tabla para los comentarios
CREATE TABLE IF NOT EXISTS public.comentarios
(
    id_comentario integer NOT NULL DEFAULT nextval('comentarios_id_comentario_seq'::regclass),
    texto text COLLATE pg_catalog."default" NOT NULL,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    id_usuario integer NOT NULL,
    id_pelicula integer NOT NULL,
    CONSTRAINT comentarios_pkey PRIMARY KEY (id_comentario),
    CONSTRAINT comentarios_id_pelicula_fkey FOREIGN KEY (id_pelicula)
        REFERENCES public.peliculas (id_pelicula) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT comentarios_id_usuario_fkey FOREIGN KEY (id_usuario)
        REFERENCES public.usuarios (id_usuario) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
