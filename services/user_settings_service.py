from sqlalchemy.orm import Session

from models.user_settings_model import UserSettings


def get_or_create_user_settings(db: Session, user_id) -> UserSettings:
    settings_row = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if settings_row is None:
        settings_row = UserSettings(user_id=user_id, two_factor_enabled=False)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row
