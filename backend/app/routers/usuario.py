from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db

router = APIRouter(prefix="/usuario", tags=["usuário"])


class ReporteUsuarioIn(BaseModel):
    latitude: float
    longitude: float
    descricao: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None


@router.post("/reportar")
def reportar_usuario(body: ReporteUsuarioIn):
    conn = get_db()
    c = conn.cursor()
    delta = 0.0009

    c.execute("""
        SELECT id, confirmacoes FROM reportes_usuario
        WHERE status = 'ativo'
          AND latitude  BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
        ORDER BY criado_em DESC LIMIT 1
    """, (
        body.latitude - delta, body.latitude + delta,
        body.longitude - delta, body.longitude + delta,
    ))
    existente = c.fetchone()

    if existente:
        c.execute("""
            UPDATE reportes_usuario
            SET confirmacoes  = confirmacoes + 1,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (existente["id"],))
        conn.commit()
        reporte_id = existente["id"]
        confirmacoes = existente["confirmacoes"] + 1
        novo = False
    else:
        c.execute("""
            INSERT INTO reportes_usuario (latitude, longitude, descricao, cidade, bairro)
            VALUES (?,?,?,?,?)
        """, (body.latitude, body.longitude, body.descricao, body.cidade, body.bairro))
        conn.commit()
        reporte_id = c.lastrowid
        confirmacoes = 1
        novo = True

    conn.close()
    return {
        "id": reporte_id,
        "novo": novo,
        "confirmacoes": confirmacoes,
        "mensagem": (
            "Novo reporte registrado! Obrigado por contribuir."
            if novo else
            f"Reporte confirmado! {confirmacoes} pessoa(s) já reportaram esta ocorrência."
        ),
    }


@router.get("/reportes")
def listar_reportes_usuario(limite: int = 100, dias: Optional[int] = None):
    conn = get_db()
    c = conn.cursor()
    if dias:
        desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            SELECT * FROM reportes_usuario
            WHERE status = 'ativo' AND criado_em >= ?
            ORDER BY confirmacoes DESC, criado_em DESC LIMIT ?
        """, (desde, limite))
    else:
        c.execute("""
            SELECT * FROM reportes_usuario
            WHERE status = 'ativo'
            ORDER BY confirmacoes DESC, criado_em DESC LIMIT ?
        """, (limite,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/reportes/{reporte_id}/confirmar")
def confirmar_reporte(reporte_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM reportes_usuario WHERE id = ?", (reporte_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Reporte não encontrado")
    c.execute("""
        UPDATE reportes_usuario
        SET confirmacoes  = confirmacoes + 1,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (reporte_id,))
    conn.commit()
    c.execute("SELECT confirmacoes FROM reportes_usuario WHERE id = ?", (reporte_id,))
    conf = c.fetchone()["confirmacoes"]
    conn.close()
    return {"id": reporte_id, "confirmacoes": conf}


@router.delete("/reportes/{reporte_id}")
def resolver_reporte(reporte_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE reportes_usuario SET status = 'resolvido' WHERE id = ?", (reporte_id,))
    conn.commit()
    conn.close()
    return {"mensagem": "Reporte marcado como resolvido"}
