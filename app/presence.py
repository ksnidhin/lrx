import datetime
from .database import save_session, log_event, is_test_user, format_time, now_utc, get_latest_event_for_users
from .notifications import notify_online, notify_offline

class SessionTracker:
    def __init__(self):
        # Maps user_id -> {"status": "ONLINE"|"OFFLINE", "started_at": iso_str}
        self.user_states = {}

    async def recover(self):
        latest = await get_latest_event_for_users()
        for uid, data in latest.items():
            if data["status"] == "ONLINE":
                self.user_states[uid] = {
                    "status": "ONLINE",
                    "started_at": data["started_at"]
                }
            else:
                self.user_states[uid] = {
                    "status": "OFFLINE",
                    "started_at": None
                }

    async def handle_status_change(self, user_id: int, new_status: str, name: str = "Unknown"):
        if not await is_test_user(user_id):
            return

        now = now_utc()
        current_state = self.user_states.get(user_id)
        current_status = current_state["status"] if current_state else "OFFLINE"

        if new_status == current_status:
            # Duplicate events are ignored for sessions, but we still log them as requested or maybe just ignore them
            # The prompt says: "Prevent duplicate sessions from duplicate Telegram updates."
            # and "duplicate online events", "duplicate offline events". We'll just return early.
            return

        await log_event(user_id, "STATE_TRANSITION", new_status, now)

        if new_status == "ONLINE" and current_status == "OFFLINE":
            # OFFLINE -> ONLINE
            self.user_states[user_id] = {
                "status": "ONLINE",
                "started_at": now
            }
            await notify_online(user_id, name, format_time(now))

        elif new_status == "OFFLINE" and current_status == "ONLINE":
            # ONLINE -> OFFLINE
            started_at = current_state["started_at"]
            
            # calculate duration
            dt_start = datetime.datetime.fromisoformat(started_at)
            dt_end = datetime.datetime.fromisoformat(now)
            duration = int((dt_end - dt_start).total_seconds())
            
            self.user_states[user_id] = {
                "status": "OFFLINE",
                "started_at": None
            }
            
            await save_session(user_id, started_at, now, duration)
            await notify_offline(user_id, name, format_time(started_at), format_time(now), duration)

tracker = SessionTracker()

# Simulation layer
async def simulate_online(user_id: int, name: str = "Simulated User"):
    await tracker.handle_status_change(user_id, "ONLINE", name)

async def simulate_offline(user_id: int, name: str = "Simulated User"):
    await tracker.handle_status_change(user_id, "OFFLINE", name)

async def simulate_duplicate_online(user_id: int, name: str = "Simulated User"):
    await tracker.handle_status_change(user_id, "ONLINE", name)
    await tracker.handle_status_change(user_id, "ONLINE", name)

async def simulate_duplicate_offline(user_id: int, name: str = "Simulated User"):
    await tracker.handle_status_change(user_id, "OFFLINE", name)
    await tracker.handle_status_change(user_id, "OFFLINE", name)
