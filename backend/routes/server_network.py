import logging
import time
import threading
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models.server import Server
from models.user import User
from routes.servers import cname, dc
from utils.minecraft_status import query_minecraft_status
from utils.security import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/servers", tags=["server-network"])

SAMPLE_INTERVAL_SECONDS = 15
HISTORY_WINDOW_SECONDS = 3 * 60 * 60
MAX_POINTS = HISTORY_WINDOW_SECONDS // SAMPLE_INTERVAL_SECONDS

history_store = defaultdict(
    lambda: {
        "timestamps": deque(maxlen=MAX_POINTS),
        "players": deque(maxlen=MAX_POINTS),
        "bandwidth_rx_bps": deque(maxlen=MAX_POINTS),
        "bandwidth_tx_bps": deque(maxlen=MAX_POINTS),
        "bandwidth_total_bps": deque(maxlen=MAX_POINTS),
    }
)
previous_network_totals = {}


def get_players_online(port: int) -> int:
    try:
        status = query_minecraft_status("127.0.0.1", int(port))
        players_info = status.get("players") or {}
        return int(players_info.get("online") or 0)
    except Exception:
        return 0


def get_container_network_totals(server_id: int) -> tuple[int, int]:
    try:
        stats = dc().api.stats(cname(server_id), stream=False)
        networks = stats.get("networks") or {}
        rx_total = 0
        tx_total = 0
        for values in networks.values():
            if not isinstance(values, dict):
                continue
            rx_total += int(values.get("rx_bytes") or 0)
            tx_total += int(values.get("tx_bytes") or 0)
        return rx_total, tx_total
    except Exception:
        return 0, 0


def sample_server_network_history():
    # Wait for tables to be created on first run
    while True:
        db = SessionLocal()
        try:
            db.query(Server).limit(1).all()
            db.close()
            break
        except Exception:
            db.close()
            time.sleep(2)

    while True:
        started_at = time.time()
        db = SessionLocal()
        try:
            servers = db.query(Server).all()
            active_ids = set()

            for server in servers:
                active_ids.add(server.id)
                timestamp = int(started_at)
                players_online = 0
                rx_bps = 0.0
                tx_bps = 0.0

                try:
                    container = dc().containers.get(cname(server.id))
                    container.reload()
                    if container.status == "running":
                        players_online = get_players_online(server.port)
                        rx_total, tx_total = get_container_network_totals(server.id)
                        previous = previous_network_totals.get(server.id)
                        if previous:
                            elapsed = max(started_at - previous["timestamp"], 1.0)
                            rx_bps = max(0.0, (rx_total - previous["rx_total"]) / elapsed)
                            tx_bps = max(0.0, (tx_total - previous["tx_total"]) / elapsed)
                        previous_network_totals[server.id] = {
                            "timestamp": started_at,
                            "rx_total": rx_total,
                            "tx_total": tx_total,
                        }
                    else:
                        previous_network_totals.pop(server.id, None)
                except Exception:
                    previous_network_totals.pop(server.id, None)

                server_history = history_store[server.id]
                server_history["timestamps"].append(timestamp)
                server_history["players"].append(players_online)
                server_history["bandwidth_rx_bps"].append(round(rx_bps, 2))
                server_history["bandwidth_tx_bps"].append(round(tx_bps, 2))
                server_history["bandwidth_total_bps"].append(round(rx_bps + tx_bps, 2))

            for stale_id in list(history_store.keys()):
                if stale_id not in active_ids:
                    history_store.pop(stale_id, None)
                    previous_network_totals.pop(stale_id, None)
        except Exception as exc:
            logger.warning("Failed to collect per-server network stats: %s", exc)
        finally:
            db.close()

        elapsed = time.time() - started_at
        time.sleep(max(1, SAMPLE_INTERVAL_SECONDS - elapsed))


_collector_thread = threading.Thread(target=sample_server_network_history, daemon=True)
_collector_thread.start()


@router.get("/{sid}/network")
def get_server_network_stats(
    sid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == sid, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server_history = history_store[sid]
    timestamps = list(server_history["timestamps"])
    players = list(server_history["players"])
    bandwidth_rx = list(server_history["bandwidth_rx_bps"])
    bandwidth_tx = list(server_history["bandwidth_tx_bps"])
    bandwidth_total = list(server_history["bandwidth_total_bps"])

    return {
        "server_id": sid,
        "window_seconds": HISTORY_WINDOW_SECONDS,
        "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS,
        "current": {
            "players_online": players[-1] if players else 0,
            "bandwidth_rx_bps": bandwidth_rx[-1] if bandwidth_rx else 0,
            "bandwidth_tx_bps": bandwidth_tx[-1] if bandwidth_tx else 0,
            "bandwidth_total_bps": bandwidth_total[-1] if bandwidth_total else 0,
        },
        "history": {
            "timestamps": timestamps,
            "players": players,
            "bandwidth_rx_bps": bandwidth_rx,
            "bandwidth_tx_bps": bandwidth_tx,
            "bandwidth_total_bps": bandwidth_total,
        },
    }
