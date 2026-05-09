import platform
import time

from docker.errors import NotFound as DockerNotFound

from .docker_client import get_docker_client

IS_DOCKER_DESKTOP_HOST = platform.system() in {"Darwin", "Windows"}
REMOVE_ATTEMPTS = 4 if IS_DOCKER_DESKTOP_HOST else 2
REMOVE_WAIT_TIMEOUT = 8.0 if IS_DOCKER_DESKTOP_HOST else 3.0
REMOVE_POLL_INTERVAL = 0.2 if IS_DOCKER_DESKTOP_HOST else 0.1


def remove_container_if_exists(name: str, *, stop_timeout: int = 10) -> bool:
    client = get_docker_client()
    last_error: Exception | None = None

    for _ in range(REMOVE_ATTEMPTS):
        try:
            container = client.containers.get(name)
        except DockerNotFound:
            return True

        try:
            if container.status == "running":
                container.stop(timeout=stop_timeout)
            container.remove(force=True)
        except DockerNotFound:
            return True
        except Exception as exc:
            last_error = exc

        deadline = time.monotonic() + REMOVE_WAIT_TIMEOUT
        while time.monotonic() < deadline:
            try:
                client.containers.get(name)
            except DockerNotFound:
                return True
            time.sleep(REMOVE_POLL_INTERVAL)

        time.sleep(0.3 if IS_DOCKER_DESKTOP_HOST else 0.1)

    if last_error:
        raise last_error
    return False
