from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import pika
import json
import os

from starlette.concurrency import run_in_threadpool
from fastapi import BackgroundTasks

from app.db import get_session
from app.models import Consulta, Medico, Paciente, Sucursal, Usuario

router = APIRouter(prefix="/api/patient", tags=["Paciente - Appointments"])


# =====================
# SCHEMAS
# =====================

class AppointmentBase(BaseModel):
    id: int
    doctor: str
    specialty: Optional[str]
    datetime: datetime
    branch: str
    room: str
    status: str


class AvailableSlot(BaseModel):
    id: int
    datetime: datetime
    branch: str
    room: str
    doctor: str
    specialty: Optional[str]


class ReserveAppointmentRequest(BaseModel):
    consulta_id: int


# =====================
# HELPERS
# =====================

async def _get_paciente_or_404(session: AsyncSession, paciente_id: int) -> Paciente:
    result = await session.execute(
        select(Paciente)
        .options(selectinload(Paciente.usuario))
        .where(
            Paciente.usuario_id == paciente_id,
            Paciente.is_activo.is_(True)
        )
    )
    paciente = result.scalar_one_or_none()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente



# =====================
# ENDPOINTS
# =====================

def send_rabbitmq_message(message: dict):
    rabbit_host = os.getenv("RABBIT_HOST", "rabbitmq")
    rabbit_queue = os.getenv("RABBIT_QUEUE", "notifications")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbit_host)
    )
    channel = connection.channel()
    channel.queue_declare(queue=rabbit_queue, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=rabbit_queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )

    connection.close()

@router.get("/{paciente_id}/appointments/upcoming", response_model=List[AppointmentBase])
async def get_upcoming(
    paciente_id: int,
    session: AsyncSession = Depends(get_session),
):
    await _get_paciente_or_404(session, paciente_id)
    now = datetime.utcnow()

    stmt = (
        select(Consulta)
        .options(
            selectinload(Consulta.medico).selectinload(Medico.usuario),
            selectinload(Consulta.sucursal),
        )
        .where(
            Consulta.paciente_id == paciente_id,
            Consulta.fecha_hora >= now,
            Consulta.estado == "reservado",
        )
        .order_by(Consulta.fecha_hora)
    )

    result = await session.execute(stmt)
    consultas = result.scalars().all()

    resp = []
    for c in consultas:
        resp.append(AppointmentBase(
            id=c.id,
            doctor=f"{c.medico.usuario.nombre} {c.medico.usuario.apellido}",
            specialty=c.especialidad,
            datetime=c.fecha_hora,
            branch=c.sucursal.nombre,
            room=c.sala,
            status="confirmed",
        ))
    return resp


@router.get("/appointments/available", response_model=List[AvailableSlot])
async def get_available(
    especialidad: Optional[str] = Query(None),
    medico_id: Optional[int] = Query(None),
    sucursal_id: Optional[int] = Query(None),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    conditions = [
        Consulta.estado == "disponible",
        Consulta.paciente_id.is_(None)
    ]

    if especialidad:
        conditions.append(Consulta.especialidad.ilike(f"%{especialidad}%"))
    if medico_id:
        conditions.append(Consulta.medico_id == medico_id)
    if sucursal_id:
        conditions.append(Consulta.sucursal_id == sucursal_id)
    if desde:
        conditions.append(Consulta.fecha_hora >= desde)
    if hasta:
        conditions.append(Consulta.fecha_hora <= hasta)

    stmt = (
        select(Consulta)
        .options(
            selectinload(Consulta.medico).selectinload(Medico.usuario),
            selectinload(Consulta.sucursal),
        )
        .where(and_(*conditions))
        .order_by(Consulta.fecha_hora)
    )

    result = await session.execute(stmt)
    consultas = result.scalars().all()

    resp = []
    for c in consultas:
        resp.append(AvailableSlot(
            id=c.id,
            datetime=c.fecha_hora,
            branch=c.sucursal.nombre,
            room=c.sala,
            doctor=f"{c.medico.usuario.nombre} {c.medico.usuario.apellido}",
            specialty=c.especialidad,
        ))
    return resp


# ==============================================
# RESERVE APPOINTMENT + RabbitMQ notification
# ==============================================
@router.post("/{paciente_id}/appointments/reserve", status_code=status.HTTP_201_CREATED)
async def reserve(
    paciente_id: int,
    body: ReserveAppointmentRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    paciente = await _get_paciente_or_404(session, paciente_id)

    stmt = (
        select(Consulta)
        .options(
            selectinload(Consulta.medico).selectinload(Medico.usuario),
            selectinload(Consulta.sucursal),
        )
        .where(Consulta.id == body.consulta_id)
        .with_for_update()
    )

    result = await session.execute(stmt)
    consulta = result.scalar_one_or_none()

    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    if consulta.estado != "disponible" or consulta.paciente_id is not None:
        raise HTTPException(status_code=409, detail="La consulta ya no está disponible")

    consulta.paciente_id = paciente_id
    consulta.estado = "reservado"

    await session.commit()

    notification = {
        "type": "appointment_reserved",
        "paciente_id": paciente_id,
        "consulta_id": consulta.id,
        "doctor": f"{consulta.medico.usuario.nombre} {consulta.medico.usuario.apellido}",
        "specialty": consulta.especialidad,
        "datetime": str(consulta.fecha_hora),
        "branch": consulta.sucursal.nombre,
        "email": paciente.usuario.email if paciente.usuario else None
    }

    #ESTO SÍ FUNCIONA — Sin bloquear el async
    background_tasks.add_task(send_rabbitmq_message, notification)

    return {"message": "Turno reservado", "consulta_id": consulta.id}


@router.post("/{paciente_id}/appointments/{consulta_id}/cancel", status_code=200)
async def cancel(
    paciente_id: int,
    consulta_id: int,
    session: AsyncSession = Depends(get_session),
):
    await _get_paciente_or_404(session, paciente_id)

    stmt = (
        select(Consulta)
        .where(Consulta.id == consulta_id)
        .with_for_update()
    )
    result = await session.execute(stmt)
    consulta = result.scalar_one_or_none()

    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    if consulta.paciente_id != paciente_id:
        raise HTTPException(status_code=403, detail="No podés cancelar este turno")

    consulta.paciente_id = None
    consulta.estado = "disponible"

    await session.commit()
    return {"message": "Turno cancelado correctamente"}
