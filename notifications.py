from flask_socketio import SocketIO, emit
from database import Session, Notification
from datetime import datetime

socketio = SocketIO()

class NotificationSystem:
    @staticmethod
    def send_notification(user_id, title, message, notification_type='info'):
        session = Session()
        try:
            # Save to database
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                created_at=datetime.utcnow()
            )
            session.add(notification)
            session.commit()

            # Emit through WebSocket
            socketio.emit('notification', {
                'title': title,
                'message': message,
                'type': notification_type,
                'timestamp': datetime.utcnow().isoformat()
            }, room=str(user_id))

        finally:
            session.close()

    @staticmethod
    def get_unread_notifications(user_id):
        session = Session()
        try:
            return session.query(Notification).filter_by(
                user_id=user_id,
                read=False
            ).all()
        finally:
            session.close() 