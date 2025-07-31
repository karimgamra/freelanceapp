from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def create_instance(db: Session, model, **data):
    try:
        instance = model(**data)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to create {model.__name__}: {e}")


def get_instance_or_404(db: Session, model, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found"
        )
    return instance


def update_instance(db: Session, instance, data: dict):
    for key, value in data.items():
        if hasattr(instance, key) and value is not None:
            setattr(instance, key, value)
    try:
        db.commit()
        db.refresh(instance)
        return instance
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to update: {e}")


def delete_instance(db: Session, instance):
    try:
        db.delete(instance)
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to delete: {e}")
