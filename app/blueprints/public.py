from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from app.models import db, Actividad

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/actividades")
def mostrar_actividades():

    actividades = Actividad.query

    text = request.args.get("busqueda")
    btnChecked = request.args.get("solo_con_plazas")

    if btnChecked:
        actividades = actividades.filter(Actividad.plazas_libres > 0)

    if text:
        actividades = actividades.filter(Actividad.nombre.contains(text))

    actividades = actividades.all()

    deporte_fav = request.cookies.get("deporte_fav")

    return render_template(
        "catalogo.html",
        lista_actividades=actividades,
        deporte_fav=deporte_fav,
    )


@public_bp.route("/actividad/<int:act_id>")
def ver_actividad(act_id):
    actividad = db.get_or_404(Actividad, act_id)
    return render_template("actividad_detalle.html", actividad=actividad)


@public_bp.route("/preferencia/<string:deporte>")
def guardar_preferencia(deporte):

    response = make_response(redirect(url_for("public.mostrar_actividades")))

    response.set_cookie(
        "deporte_fav", deporte, max_age=60 * 60 * 24 * 15, samesite="Lax", httponly=True
    )

    return response


@public_bp.route("/limpiar-preferencia")
def limpiar_preferencia():

    respuesta = make_response(redirect(url_for("public.mostrar_actividades")))
    respuesta.delete_cookie("deporte_fav")

    return respuesta


@public_bp.route("/reservas/apuntar/<int:act_id>", methods=["POST"])
@login_required
def apuntar_actividad(act_id):

    actividad = db.get_or_404(Actividad, act_id)

    if "reservas" not in session:
        session["reservas"] = []

    session.permanent = True

    if actividad.plazas_libres <= 0:
        flash("La actividad no tiene plazas libres", "error")

    elif act_id in session["reservas"]:
        flash("La actividad ya esta en sus reservas", "error")

    elif len(session["reservas"]) >= 3:
        flash(
            "Superas el limite de actividades a la que puedes estar apuntado", "error"
        )
    else:
        session["reservas"].append(actividad.id)
        session.modified = True
        flash(
            f"Se ha añadido de forma exitosa la actividad {actividad.nombre} a sus reservas",
            "exito",
        )

    return redirect(url_for("public.mostrar_actividades"))


@public_bp.route("/reservas")
@login_required
def ver_reservas():

    if "reservas" not in session:
        session["reservas"] = []

    session.permanent = True

    total_sin_descuento = 0.0
    descuento_aplicado = False
    total_final = 0.0

    actividades = Actividad.query.filter(Actividad.id.in_(session["reservas"]))

    for actividad in actividades:
        total_sin_descuento += actividad.cuota

    if len(session["reservas"]) == 3:
        descuento_aplicado = True
        total_final = total_sin_descuento * 0.8
    else:
        total_final = total_sin_descuento

    actividades = actividades.all()

    return render_template(
        "reservas.html",
        actividades=actividades,
        total_sin_descuento=total_sin_descuento,
        descuento_aplicado=descuento_aplicado,
        total_final=total_final,
    )


@public_bp.route("/reservas/cancelar/<int:act_id>", methods=["POST"])
@login_required
def cancelar_reserva(act_id):

    actividad = db.get_or_404(Actividad, act_id)

    if "reservas" not in session:
            session["reservas"] = []
    
    session.permanent = True

    if actividad.id in session["reservas"]:
        session["reservas"].remove(act_id)
        session.modified = True

        flash("Cancelación de reserva exitosa", "exito")
    return redirect(url_for("public.ver_reservas"))


@public_bp.route("/reservas/confirmar", methods=["POST"])
@login_required
def confirmar_reservas():

    if "reservas" not in session:
            session["reservas"] = []
    
    session.permanent = True
    
    actividades = Actividad.query.filter(Actividad.id.in_(session["reservas"]))
    
    for actividad in actividades:
        actividad.plazas_libres -= 1

    db.session.commit()
    session.pop("reservas", None)

    return redirect(url_for("public.mostrar_actividades"))
