from flask_socketio import SocketIO, emit, join_room, leave_room
from database import Session, Notification, NotificationPreference
import json
from datetime import datetime

class EnhancedNotificationSystem:
    def __init__(self, socketio):
        self.socketio = socketio
        self.session = Session()

    def send_notification(self, user_id, data, notification_type='info', priority='normal'):
        # Create notification object
        notification = Notification(
            user_id=user_id,
            title=data['title'],
            message=data['message'],
            type=notification_type,
            priority=priority,
            created_at=datetime.utcnow(),
            metadata=json.dumps(data.get('metadata', {}))
        )

        # Check user preferences
        preferences = self.get_user_preferences(user_id)
        if self.should_send_notification(notification, preferences):
            # Save to database
            self.session.add(notification)
            self.session.commit()

            # Send through appropriate channels
            self.send_through_channels(notification, preferences)

    def send_through_channels(self, notification, preferences):
        # Real-time WebSocket notification
        if preferences.get('real_time_enabled', True):
            self.socketio.emit('notification', 
                self.format_notification(notification),
                room=str(notification.user_id)
            )

        # Email notification for high priority
        if notification.priority == 'high' and preferences.get('email_enabled', True):
            self.send_email_notification(notification)

        # Push notification
        if preferences.get('push_enabled', True):
            self.send_push_notification(notification)

    def format_notification(self, notification):
        return {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'priority': notification.priority,
            'timestamp': notification.created_at.isoformat(),
            'metadata': json.loads(notification.metadata)
        }

    def send_bulk_notification(self, user_ids, data):
        for user_id in user_ids:
            self.send_notification(user_id, data)

    def mark_as_read(self, notification_id, user_id):
        notification = self.session.query(Notification).get(notification_id)
        if notification and notification.user_id == user_id:
            notification.read = True
            self.session.commit() 