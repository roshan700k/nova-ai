from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from api.auth import current_user
from database.database import (
    list_tasks, create_task, update_task, delete_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _uid(request: Request):
    user = current_user(request)
    return user["id"] if user else None


@router.get("")
def get_tasks(request: Request):
    return {"tasks": list_tasks(_uid(request))}


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    notes: str = Field(default="", max_length=2000)
    due: str = Field(default="", max_length=100)


@router.post("")
def add_task(data: TaskIn, request: Request):
    title = data.title.strip()
    if not title:
        return {"error": "title required"}
    task_id = create_task(_uid(request), title, data.notes.strip(), data.due.strip())
    return {"ok": True, "id": task_id}


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)
    due: str | None = Field(default=None, max_length=100)
    done: bool | None = None


@router.put("/{task_id}")
def edit_task(task_id: int, data: TaskUpdate, request: Request):
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    if not fields:
        return {"error": "nothing to update"}
    update_task(task_id, _uid(request), fields)
    return {"ok": True}


@router.delete("/{task_id}")
def remove_task(task_id: int, request: Request):
    delete_task(task_id, _uid(request))
    return {"ok": True}
