# app/seed_data.py
import asyncio
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.db import engine, Base, AsyncSessionLocal
from app.models import (
    Usuario,
    Admin,
    Medico,
    Paciente,
    Sucursal,
    Consulta,
    Estudio,
    SucursalEstudio,
    Medicamento,
    Compra,
    Receta,
    RecetaMedicamento,
)


async def seed():
    async with engine.begin() as conn:
        print(">>> Creando tablas...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print(">>> Insertando datos...")

        # ======================================
        # USUARIOS
        # ======================================
        admin_user = Usuario(
            nombre="Paula",
            apellido="Admin",
            cedula="12345678",
            email="admin@example.com",
            fecha_nac=date(1990, 1, 1),
            celular="099111111",
            rol="admin",
        )
        session.add(admin_user)
        await session.flush()
        session.add(Admin(usuario_id=admin_user.id))

        medico_user = Usuario(
            nombre="Juan",
            apellido="Pérez",
            cedula="45678912",
            email="medico@example.com",
            fecha_nac=date(1985, 5, 20),
            celular="098222222",
            rol="medico",
        )
        session.add(medico_user)
        await session.flush()
        session.add(Medico(
            usuario_id=medico_user.id,
            especialidades=["cardiología", "pediatría"]
        ))

        paciente_user = Usuario(
            nombre="María",
            apellido="Gómez",
            cedula="98765432",
            email="luciaeboli12@gmail.com",
            fecha_nac=date(1995, 3, 14),
            celular="097333333",
            rol="paciente",
        )
        session.add(paciente_user)
        await session.flush()
        session.add(Paciente(usuario_id=paciente_user.id))

        # ======================================
        # SUCURSALES
        # ======================================
        s1 = Sucursal(
            nombre="Sucursal Centro",
            direccion="Av. Principal 123",
            hora_desde=time(8, 0),
            hora_hasta=time(18, 0)
        )
        s2 = Sucursal(
            nombre="Sucursal Carrasco",
            direccion="Av. Rivera 456",
            hora_desde=time(9, 0),
            hora_hasta=time(19, 0)
        )
        session.add_all([s1, s2])
        await session.flush()

        # ======================================
        # CONSULTA RESERVADA (ejemplo)
        # ======================================
        consulta1 = Consulta(
            sucursal_id=s1.id,
            medico_id=medico_user.id,
            paciente_id=paciente_user.id,
            fecha_hora=datetime.utcnow() + timedelta(days=1),
            sala="Sala 1",
            especialidad="cardiología",
            estado="reservado",
        )
        session.add(consulta1)

        # ======================================
        # CONSULTAS DISPONIBLES (para probar reserva)
        # ======================================
        available_slots = []
        now = datetime.utcnow()

        for i in range(3):
            available_slots.append(
                Consulta(
                    sucursal_id=s1.id,
                    medico_id=medico_user.id,
                    paciente_id=None,
                    fecha_hora=now + timedelta(days=1, hours=i+1),
                    sala=f"Sala {i+2}",
                    especialidad="cardiología",
                    estado="disponible",
                )
            )

        session.add_all(available_slots)

        # ======================================
        # ESTUDIOS
        # ======================================
        estudio1 = Estudio(
            nombre="Electrocardiograma",
            fecha=date.today() + timedelta(days=3),
            hora=time(14, 30),
            medico_id=medico_user.id,
            paciente_id=paciente_user.id,
        )
        session.add(estudio1)
        await session.flush()

        session.add(SucursalEstudio(
            sucursal_id=s1.id,
            estudio_id=estudio1.id
        ))

        # ======================================
        # MEDICAMENTOS
        # ======================================
        paracetamol = Medicamento(
            nombre="Paracetamol 500mg",
            precio=Decimal("150.00")
        )
        ibuprofeno = Medicamento(
            nombre="Ibuprofeno 400mg",
            precio=Decimal("200.00")
        )
        session.add_all([paracetamol, ibuprofeno])
        await session.flush()

        # ======================================
        # RECETAS
        # ======================================
        receta1 = Receta(
            medico_id=medico_user.id,
            paciente_id=paciente_user.id,
            desde=date.today(),
            hasta=date.today() + timedelta(days=5),
            frecuencia="Cada 8 horas"
        )
        session.add(receta1)
        await session.flush()

        session.add_all([
            RecetaMedicamento(receta_id=receta1.id, medicamento_id=paracetamol.id),
            RecetaMedicamento(receta_id=receta1.id, medicamento_id=ibuprofeno.id),
        ])

        # ======================================
        # COMPRAS
        # ======================================
        compra1 = Compra(
            paciente_id=paciente_user.id,
            medicamento_id=paracetamol.id,
            cantidad=1,
        )
        session.add(compra1)

        await session.commit()
        print(">>> Seed completado con éxito")


if __name__ == "__main__":
    asyncio.run(seed())
