"""Admin API: user management, feature flags, system control."""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database.database import connect
from api.auth import current_user, require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


class FeatureFlag(BaseModel):
    name: str
    enabled: bool = True
    description: str = ""


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


def get_conn():
    conn = connect()
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/users")
def list_users(admin=Depends(require_admin)):
    """List all users (admin only)."""
    conn = get_conn()
    rows = conn.execute("SELECT id, email, name, provider, role, is_active, created_at FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return {"users": [dict(r) for r in rows]}


@router.put("/users/{user_id}")
def update_user(user_id: int, update: UserUpdate, admin=Depends(require_admin)):
    """Update user role/status (admin only)."""
    conn = get_conn()
    updates = []
    params = []
    if update.name is not None:
        updates.append("name = ?")
        params.append(update.name)
    if update.role is not None:
        updates.append("role = ?")
        params.append(update.role)
    if update.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if update.is_active else 0)
    if not updates:
        conn.close()
        raise HTTPException(400, "No updates provided")
    params.append(user_id)
    conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/features")
def list_features(admin=Depends(require_admin)):
    """List all feature flags (admin only)."""
    conn = get_conn()
    rows = conn.execute("SELECT name, enabled, description FROM features ORDER BY name").fetchall()
    conn.close()
    return {"features": [dict(r) for r in rows]}


@router.put("/features/{name}")
def update_feature(name: str, flag: FeatureFlag, admin=Depends(require_admin)):
    """Enable/disable feature (admin only)."""
    conn = get_conn()
    conn.execute(
        "INSERT INTO features (name, enabled, description) VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET enabled = ?, description = ?",
        (name, 1 if flag.enabled else 0, flag.description, 1 if flag.enabled else 0, flag.description)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "name": name, "enabled": flag.enabled}


@router.get("/stats")
def admin_stats(admin=Depends(require_admin)):
    """System stats (admin only)."""
    conn = get_conn()
    users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    active_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE is_active = 1").fetchone()["c"]
    memories = conn.execute("SELECT COUNT(*) as c FROM memory").fetchone()["c"]
    conn.close()
    return {
        "total_users": users,
        "active_users": active_users,
        "total_memories": memories,
    }
