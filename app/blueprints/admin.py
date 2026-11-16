import os
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
from app.models import db, login_manager, Actividad
from app.forms import ActividadForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def ir_al_login():
    if not current_user.is_authenticated:
        login_manager.unauthorized()

    if not current_user.es_monitor:
        abort(403)


@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()
    if form.validate_on_submit():
        directorio = current_app.config["UPLOAD_FOLDER"]

        nombre_seguro = secure_filename(form.archivo_imagen.data.filename)
        deporte = form.deporte.data.lower()
        nombre_final = f"{deporte}_{nombre_seguro}"

        ruta = os.path.join(directorio, nombre_final)
        form.archivo_imagen.data.save(ruta)

    nombre = form.nombre.data
    deporte_actividad = form.deporte.data
    cuota = form.cuota.data
    plazas_libres = form.plazas_libres.data
    imagen = nombre_final

    actividad = Actividad(
        nombre=nombre,
        deporte=deporte_actividad,
        cuota=cuota,
        plazas_libres=plazas_libres,
        imagen=imagen,
    )

    db.session.add(actividad)
    db.session.commit()

    flash("Actividad creada correctamente.", "success")

    return redirect(url_for("public.mostrar_actividades"))


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad)

    if form.validate_on_submit():
        imagen_temporal = actividad.imagen
        if form.archivo_imagen.data:
            directorio = current_app.config["UPLOAD_FOLDER"]

            nombre_seguro = secure_filename(form.archivo_imagen.data.filename)
            deporte = form.deporte.data.lower()
            nombre_final = f"{deporte}_{nombre_seguro}"

            ruta = os.path.join(directorio, nombre_final)
            form.archivo_imagen.data.save(ruta)

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):
    flash("Eliminación pendiente de implementar.", "info")
    return redirect(url_for("public.mostrar_actividades"))
