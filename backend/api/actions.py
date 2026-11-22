from fastapi import APIRouter

from services.actions import broker

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/pending")
def pending():
    return {"actions": broker.list_pending()}


@router.post("/{action_id}/approve")
def approve(action_id: str):
    return broker.approve(action_id)


@router.post("/{action_id}/deny")
def deny(action_id: str):
    return broker.deny(action_id)
