import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.presence import SessionTracker, simulate_online, simulate_offline, tracker
from app.telegram_client import handler
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently

@pytest.fixture(autouse=True)
def setup_tracker(mocker):
    tracker.user_states.clear()
    
    # Mock all database calls so we don't need SQLite in tests
    mocker.patch('app.presence.is_test_user', new_callable=AsyncMock, return_value=True)
    mocker.patch('app.presence.log_event', new_callable=AsyncMock)
    mocker.patch('app.presence.save_session', new_callable=AsyncMock)

@pytest.mark.asyncio
async def test_offline_to_online(mocker):
    notify_mock = mocker.patch('app.presence.notify_online', new_callable=AsyncMock)
    
    await simulate_online(123, "Test")
    
    assert tracker.user_states[123]["status"] == "ONLINE"
    notify_mock.assert_called_once()

@pytest.mark.asyncio
async def test_online_to_offline(mocker):
    mocker.patch('app.presence.notify_online', new_callable=AsyncMock)
    notify_mock = mocker.patch('app.presence.notify_offline', new_callable=AsyncMock)
    save_mock = mocker.patch('app.presence.save_session', new_callable=AsyncMock)
    
    await simulate_online(123, "Test")
    await simulate_offline(123, "Test")
    
    assert tracker.user_states[123]["status"] == "OFFLINE"
    save_mock.assert_called_once()
    assert save_mock.call_args[0][0] == 123
    assert save_mock.call_args[0][3] >= 0  # duration
    notify_mock.assert_called_once()

@pytest.mark.asyncio
async def test_duplicate_online_events(mocker):
    notify_mock = mocker.patch('app.presence.notify_online', new_callable=AsyncMock)
    
    await simulate_online(123, "Test")
    await simulate_online(123, "Test")
    
    # Should only notify once
    assert notify_mock.call_count == 1
    assert tracker.user_states[123]["status"] == "ONLINE"

@pytest.mark.asyncio
async def test_duplicate_offline_events(mocker):
    mocker.patch('app.presence.notify_online', new_callable=AsyncMock)
    notify_mock = mocker.patch('app.presence.notify_offline', new_callable=AsyncMock)
    
    await simulate_online(123, "Test")
    await simulate_offline(123, "Test")
    await simulate_offline(123, "Test")
    
    # Should only notify offline once
    assert notify_mock.call_count == 1
    assert tracker.user_states[123]["status"] == "OFFLINE"

@pytest.mark.asyncio
async def test_multiple_test_accounts(mocker):
    mocker.patch('app.presence.notify_online', new_callable=AsyncMock)
    
    await simulate_online(111)
    await simulate_online(222)
    
    assert tracker.user_states[111]["status"] == "ONLINE"
    assert tracker.user_states[222]["status"] == "ONLINE"

@pytest.mark.asyncio
async def test_duration_calculation(mocker):
    mocker.patch('app.presence.notify_online', new_callable=AsyncMock)
    mocker.patch('app.presence.notify_offline', new_callable=AsyncMock)
    save_mock = mocker.patch('app.presence.save_session', new_callable=AsyncMock)
    
    import app.presence
    import datetime
    
    base_time = datetime.datetime(2025, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    
    with patch('app.presence.now_utc') as mock_now:
        mock_now.return_value = base_time.isoformat()
        await simulate_online(123)
        
        mock_now.return_value = (base_time + datetime.timedelta(seconds=42)).isoformat()
        await simulate_offline(123)
        
    assert save_mock.call_args[0][3] == 42

@pytest.mark.asyncio
async def test_restart_recovery(mocker):
    # Mock get_latest_event_for_users
    latest_mock = {"status": "ONLINE", "started_at": "2025-01-01T12:00:00+00:00"}
    mocker.patch('app.presence.get_latest_event_for_users', new_callable=AsyncMock, return_value={123: latest_mock})
    
    new_tracker = SessionTracker()
    await new_tracker.recover()
    
    assert new_tracker.user_states[123]["status"] == "ONLINE"
    assert new_tracker.user_states[123]["started_at"] is not None

@pytest.mark.asyncio
async def test_unavailable_status(mocker):
    tracker_mock = mocker.patch('app.telegram_client.tracker.handle_status_change', new_callable=AsyncMock)
    
    class FakeEvent:
        user_id = 123
        status = UserStatusRecently()
        
    mocker.patch('app.telegram_client.client.get_entity', new_callable=AsyncMock)
    
    await handler(FakeEvent())
    tracker_mock.assert_not_called()

@pytest.mark.asyncio
async def test_admin_authorization(mocker):
    from app.bot import is_admin
    class FakeMessageEvent:
        def __init__(self, chat_id):
            self.chat_id = chat_id
            
    mocker.patch('app.bot.ADMIN_CHAT_ID', 999)
    
    assert is_admin(FakeMessageEvent(999)) == True
    assert is_admin(FakeMessageEvent(111)) == False

@pytest.mark.asyncio
async def test_notification_generation(mocker):
    import app.notifications as notif
    send_mock = mocker.patch('app.notifications.send_telegram_notification', new_callable=AsyncMock)
    
    await notif.notify_online(123, "Test", "2025-01-01")
    send_mock.assert_called_once()
    assert "ONLINE" in send_mock.call_args[0][0]
    
    send_mock.reset_mock()
    await notif.notify_offline(123, "Test", "2025-01-01", "2025-01-02", 3600)
    send_mock.assert_called_once()
    assert "OFFLINE" in send_mock.call_args[0][0]
    assert "3600 seconds" in send_mock.call_args[0][0]
