import asyncio
from datetime import timedelta
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models.server import Server
from models.server_task import ServerTask
from models.user import User
from routes import tasks


class ScheduledTaskClaimTests(unittest.TestCase):
    def test_stale_due_id_cannot_execute_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(
                f"sqlite:///{os.path.join(directory, 'tasks.db')}",
                connect_args={"check_same_thread": False},
            )
            session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            Base.metadata.create_all(engine)
            session = session_factory()
            user = User(username="owner", email="owner@example.com", hashed_password="unused")
            session.add(user)
            session.flush()
            server = Server(name="test", owner_id=user.id)
            session.add(server)
            session.flush()
            task = ServerTask(
                server_id=server.id,
                name="command",
                action="command",
                command="say once",
                interval_minutes=60,
                schedule_mode="interval",
                enabled=True,
                next_run_at=tasks.utcnow() - timedelta(minutes=1),
            )
            session.add(task)
            session.commit()
            task_id = task.id
            session.close()

            command = AsyncMock()
            with patch.object(tasks, "SessionLocal", session_factory), patch.object(
                tasks, "send_console_command", command
            ):
                first = asyncio.run(tasks.execute_server_task(task_id))
                second = asyncio.run(tasks.execute_server_task(task_id))

            self.assertTrue(first[0])
            self.assertFalse(second[0])
            self.assertEqual(command.await_count, 1)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
