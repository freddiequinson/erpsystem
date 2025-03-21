from extensions import db
from datetime import datetime

class Activity(db.Model):
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(128), nullable=False)
    details = db.Column(db.Text, nullable=True)
    user = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activity_type = db.Column(db.String(32), nullable=True)
    
    @classmethod
    def log(cls, description, details=None, user=None, activity_type=None):
        """Helper method to quickly log an activity"""
        activity = cls(
            description=description,
            details=details,
            user=user,
            activity_type=activity_type
        )
        db.session.add(activity)
        try:
            db.session.commit()
            return activity
        except Exception as e:
            db.session.rollback()
            print(f"Error logging activity: {str(e)}")
            return None

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(128), nullable=True)
    event_type = db.Column(db.String(32), nullable=True)
    created_by = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_past(self):
        """Check if the event is in the past"""
        return self.date < datetime.utcnow()
    
    @property
    def is_today(self):
        """Check if the event is today"""
        today = datetime.utcnow().date()
        return self.date.date() == today
