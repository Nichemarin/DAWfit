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


@admin_bp.route("/actividad/nueva", methods=["GET", "POST"])
def crear_actividad():
    form = ActividadForm()

    ruta = current_app.config["UPLOAD_FOLDER"]
    if form.validate_on_submit():
        nombre_final = None

        if form.archivo_imagen.data:
            minuscula = form.deporte.data.lower()
            nombre_seguro = secure_filename(form.archivo_imagen.data.filename)
            nombre_final = f"{minuscula}_{nombre_seguro}"

            form.archivo_imagen.data.save(os.path.join(ruta, nombre_final))

        actividad = Actividad(
            nombre=form.nombre.data,
            deporte=form.deporte.data,
            cuota=form.cuota.data,
            plazas_libres=form.plazas_libres.data,
            imagen=nombre_final,
        )

        db.session.add(actividad)
        db.session.commit()

    return render_template(
        "actividad_form.html", form=form, titulo="Nueva Actividad Deportiva"
    )


@admin_bp.route("/actividad/<int:act_id>/editar", methods=["GET", "POST"])
def editar_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    form = ActividadForm(obj=actividad)

    ruta = current_app.config["UPLOAD_FOLDER"]

    if form.validate_on_submit():
        nombre_final = None
        imagen_temporal = actividad.imagen

        if form.archivo_imagen.data:
            minuscula = form.deporte.data.lower()
            nombre_seguro = secure_filename(form.archivo_imagen.data.filename)
            nombre_final = f"{minuscula}_{nombre_seguro}"

            if imagen_temporal != nombre_final:
                if imagen_temporal is not None:
                    ruta_antigua = os.path.join(ruta, imagen_temporal)
                    form.archivo_imagen.data.save(os.path.join(ruta, nombre_final))
                    if os.path.exists(ruta_antigua):
                        os.remove(ruta_antigua)
                actividad.imagen = nombre_final

        actividad.nombre = form.nombre.data
        actividad.deporte = form.deporte.data
        actividad.cuota = form.cuota.data
        actividad.plazas_libres = form.plazas_libres.data

        db.session.commit()

    return render_template(
        "actividad_form.html",
        form=form,
        titulo="Editar Actividad",
        actividad=actividad,
    )


@admin_bp.route("/actividad/<int:act_id>/eliminar", methods=["POST"])
def eliminar_actividad(act_id):

    actividad = db.get_or_404(Actividad, act_id)

    if actividad.plazas_libres == 0:
        flash(
            "No se ha podido eliminar la actividad",
            "error",
        )
        return redirect(url_for("public.mostrar_actividades"))

    else:
        ruta = current_app.config["UPLOAD_FOLDER"]

        if actividad.imagen is not None:
            ruta_borrar = os.path.join(ruta, actividad.imagen)
            if os.path.exists(ruta_borrar):
                os.remove(ruta_borrar)

        db.session.delete(actividad)
        db.session.commit()
    return redirect(url_for("public.mostrar_actividades"))


@admin_bp.before_request
def comprobacion():

    if not current_user.is_authenticated:
        return login_manager.unauthorized()

    if not current_user.es_monitor:
        abort(403)
