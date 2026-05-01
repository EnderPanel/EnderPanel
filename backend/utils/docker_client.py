from functools import lru_cache

import docker


@lru_cache(maxsize=1)
def get_docker_client():
    return docker.from_env()


def close_docker_client() -> None:
    try:
        client = get_docker_client()
    except Exception:
        return

    try:
        client.close()
    except Exception:
        pass

    get_docker_client.cache_clear()
