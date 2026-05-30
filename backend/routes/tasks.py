from datetime import datetime, time as datetime_time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models.server import Server
from models.server_task import ServerTask
from models.user import User
from utils.security import get_current_user
from .console import ConsoleCommandRequest, send_console_command
from .files import create_backup
from .servers import restart_server, start_server, stop_server


router = APIRouter(prefix="/api/servers", tags=["tasks"])

TASK_ACTIONS = {"start", "stop", "restart", "backup", "command"}
SCHEDULE_MODES = {"interval", "specific_time"}
MIN_TASK_INTERVAL_MINUTES = 5
MAX_TASK_INTERVAL_MINUTES = 10080
DEFAULT_RUN_DAYS = [0, 1, 2, 3, 4, 5, 6]


def utcnow() -> datetime:
    return datetime.utcnow()


def local_timezone():
    return datetime.now().astimezone().tzinfo or timezone.utc


def next_run_for_interval(interval_minutes: int, *, base: datetime | None = None) -> datetime:
    return (base or utcnow()) + timedelta(minutes=interval_minutes)


def parse_run_days(raw: str | None) -> list[int]:
    if not raw:
        return []
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            day = int(part)
        except ValueError:
            continue
        if 0 <= day <= 6 and day not in values:
            values.append(day)
    return sorted(values)


def encode_run_days(days: list[int] | None) -> str | None:
    normalized = sorted({int(day) for day in (days or []) if 0 <= int(day) <= 6})
    if not normalized:
        return None
    return ",".join(str(day) for day in normalized)


def parse_run_time(raw: str | None) -> datetime_time | None:
    if not raw:
        return None
    try:
        hour_text, minute_text = raw.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (ValueError, AttributeError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return datetime_time(hour=hour, minute=minute)


def next_run_for_specific_time(
    run_time: str,
    run_days: list[int],
    *,
    base: datetime | None = None,
) -> datetime:
    target_time = parse_run_time(run_time)
    if target_time is None:
        raise ValueError("Scheduled time is invalid")
    if not run_days:
        raise ValueError("At least one run day is required")

    tz = local_timezone()
    base_utc = (base or utcnow()).replace(tzinfo=timezone.utc)
    local_now = base_utc.astimezone(tz)

    for offset in range(0, 15):
        candidate_date = local_now.date() + timedelta(days=offset)
        if candidate_date.weekday() not in run_days:
            continue

        candidate_local = datetime.combine(candidate_date, target_time, tzinfo=tz)
        if candidate_local > local_now:
            return candidate_local.astimezone(timezone.utc).replace(tzinfo=None)

    raise ValueError("Could not calculate the next scheduled run")


def next_run_for_schedule(
    *,
    schedule_mode: str,
    interval_minutes: int,
    run_time: str | None,
    run_days: list[int],
    base: datetime | None = None,
) -> datetime:
    if schedule_mode == "specific_time":
        return next_run_for_specific_time(run_time or "", run_days, base=base)
    return next_run_for_interval(interval_minutes, base=base)


def serialize_task(task: ServerTask) -> dict:
    return {
        "id": task.id,
        "server_id": task.server_id,
        "name": task.name,
        "action": task.action,
        "interval_minutes": task.interval_minutes,
        "schedule_mode": task.schedule_mode or "interval",
        "run_time": task.run_time,
        "run_days": parse_run_days(task.run_days),
        "enabled": bool(task.enabled),
        "command": task.command,
        "last_status": task.last_status,
        "last_error": task.last_error,
        "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
        "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def get_owned_server(db: Session, sid: int, user: User) -> Server:
    server = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


def get_owned_task(db: Session, sid: int, task_id: int, user: User) -> ServerTask:
    task = (
        db.query(ServerTask)
        .join(Server, Server.id == ServerTask.server_id)
        .filter(ServerTask.id == task_id, ServerTask.server_id == sid, Server.owner_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


class ServerTaskPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=20)
    schedule_mode: str = Field(default="interval", min_length=1, max_length=20)
    interval_minutes: int | None = Field(default=60)
    run_time: str | None = Field(default=None, max_length=5)
    run_days: list[int] = Field(default_factory=list)
    enabled: bool = True
    command: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Task name is required")
        return normalized

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in TASK_ACTIONS:
            raise ValueError("Unsupported task action")
        return normalized

    @field_validator("schedule_mode")
    @classmethod
    def validate_schedule_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SCHEDULE_MODES:
            raise ValueError("Unsupported schedule mode")
        return normalized

    @field_validator("interval_minutes")
    @classmethod
    def validate_interval_minutes(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < MIN_TASK_INTERVAL_MINUTES or value > MAX_TASK_INTERVAL_MINUTES:
            raise ValueError("Interval is out of range")
        return int(value)

    @field_validator("run_time")
    @classmethod
    def validate_run_time(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if parse_run_time(normalized) is None:
            raise ValueError("Scheduled time must be in HH:MM format")
        return normalized

    @field_validator("run_days")
    @classmethod
    def validate_run_days(cls, value: list[int]) -> list[int]:
        normalized = sorted({int(day) for day in (value or [])})
        if any(day < 0 or day > 6 for day in normalized):
            raise ValueError("Run days must be between 0 and 6")
        return normalized

    @field_validator("command")
    @classmethod
    def normalize_command(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_command_requirements(self):
        if self.action == "command" and not self.command:
            raise ValueError("Command tasks require a console command")
        if self.action != "command":
            self.command = None
        if self.schedule_mode == "interval":
            if self.interval_minutes is None:
                raise ValueError("Interval schedules require a repeat interval")
            self.run_time = None
            self.run_days = []
        else:
            if not self.run_time:
                raise ValueError("Time-based schedules require a run time")
            if not self.run_days:
                raise ValueError("Time-based schedules require at least one day")
            if self.interval_minutes is None:
                self.interval_minutes = 60
        return self


async def execute_server_task(task_id: int, *, manual: bool = False) -> tuple[bool, str | None]:
    db = SessionLocal()
    try:
        task = db.query(ServerTask).filter(ServerTask.id == task_id).first()
        if not task:
            return False, "Task not found"

        server = db.query(Server).filter(Server.id == task.server_id).first()
        if not server:
            task.last_status = "failed"
            task.last_error = "Server not found"
            db.commit()
            return False, task.last_error

        owner = db.query(User).filter(User.id == server.owner_id).first()
        if not owner:
            task.last_status = "failed"
            task.last_error = "Server owner not found"
            db.commit()
            return False, task.last_error

        now = utcnow()
        task.last_status = "running"
        task.last_error = None
        task.last_run_at = now
        if task.enabled:
            task.next_run_at = next_run_for_schedule(
                schedule_mode=task.schedule_mode or "interval",
                interval_minutes=task.interval_minutes,
                run_time=task.run_time,
                run_days=parse_run_days(task.run_days),
                base=now,
            )
        elif manual:
            task.next_run_at = task.next_run_at
        else:
            task.next_run_at = None
        db.commit()

        try:
            if task.action == "start":
                await start_server(sid=server.id, data=None, db=db, user=owner)
            elif task.action == "stop":
                stop_server(server.id, db=db, user=owner)
            elif task.action == "restart":
                await restart_server(server.id, db=db, user=owner)
            elif task.action == "backup":
                create_backup(server.id, db=db, current_user=owner)
            elif task.action == "command":
                await send_console_command(
                    server.id,
                    payload=ConsoleCommandRequest(command=task.command or ""),
                    db=db,
                    user=owner,
                )

            task.last_status = "success"
            task.last_error = None
            db.commit()
            return True, None
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Task execution failed"
            task.last_status = "failed"
            task.last_error = detail
            db.commit()
            return False, detail
        except Exception as exc:
            task.last_status = "failed"
            task.last_error = str(exc)
            db.commit()
            return False, str(exc)
    finally:
        db.close()


async def run_due_server_tasks_once() -> None:
    db = SessionLocal()
    try:
        now = utcnow()
        due_ids = [
            row.id
            for row in (
                db.query(ServerTask)
                .filter(
                    ServerTask.enabled.is_(True),
                    ServerTask.next_run_at.isnot(None),
                    ServerTask.next_run_at <= now,
                )
                .order_by(ServerTask.next_run_at.asc(), ServerTask.id.asc())
                .limit(10)
                .all()
            )
        ]
    finally:
        db.close()

    for task_id in due_ids:
        await execute_server_task(task_id)


@router.get("/{sid}/tasks")
def list_server_tasks(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_server(db, sid, user)
    tasks = (
        db.query(ServerTask)
        .filter(ServerTask.server_id == sid)
        .order_by(ServerTask.created_at.desc(), ServerTask.id.desc())
        .all()
    )
    return [serialize_task(task) for task in tasks]


@router.post("/{sid}/tasks")
def create_server_task(
    sid: int,
    payload: ServerTaskPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_owned_server(db, sid, user)
    now = utcnow()
    task = ServerTask(
        server_id=sid,
        name=payload.name,
        action=payload.action,
        interval_minutes=payload.interval_minutes,
        schedule_mode=payload.schedule_mode,
        run_time=payload.run_time,
        run_days=encode_run_days(payload.run_days),
        enabled=payload.enabled,
        command=payload.command,
        last_status="idle",
        next_run_at=next_run_for_schedule(
            schedule_mode=payload.schedule_mode,
            interval_minutes=payload.interval_minutes or 60,
            run_time=payload.run_time,
            run_days=payload.run_days,
            base=now,
        ) if payload.enabled else None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return serialize_task(task)


@router.put("/{sid}/tasks/{task_id}")
def update_server_task(
    sid: int,
    task_id: int,
    payload: ServerTaskPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = get_owned_task(db, sid, task_id, user)
    now = utcnow()
    task.name = payload.name
    task.action = payload.action
    task.interval_minutes = payload.interval_minutes or 60
    task.schedule_mode = payload.schedule_mode
    task.run_time = payload.run_time
    task.run_days = encode_run_days(payload.run_days)
    task.enabled = payload.enabled
    task.command = payload.command
    task.next_run_at = next_run_for_schedule(
        schedule_mode=payload.schedule_mode,
        interval_minutes=payload.interval_minutes or 60,
        run_time=payload.run_time,
        run_days=payload.run_days,
        base=now,
    ) if payload.enabled else None
    if not task.enabled and task.last_status == "running":
        task.last_status = "disabled"
    db.commit()
    db.refresh(task)
    return serialize_task(task)


@router.delete("/{sid}/tasks/{task_id}")
def delete_server_task(
    sid: int,
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = get_owned_task(db, sid, task_id, user)
    db.delete(task)
    db.commit()
    return {"status": "deleted"}


@router.post("/{sid}/tasks/{task_id}/run")
async def run_server_task_now(
    sid: int,
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task = get_owned_task(db, sid, task_id, user)
    ok, error = await execute_server_task(task.id, manual=True)
    db.expire_all()
    task = get_owned_task(db, sid, task_id, user)
    if not ok:
        raise HTTPException(status_code=400, detail=error or "Task execution failed")
    return serialize_task(task)
