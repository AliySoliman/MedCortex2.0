from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.repositories.memory_repository import MemoryRepository
from app.models.user_preference import UserPreference


class UserMemory(ABC):
    """Abstract base class for user memory engines."""
    
    @abstractmethod
    def store_user_info(
        self,
        user_id: str,
        info: Dict[str, Any],
    ):
        """Store user information."""
        pass
    
    @abstractmethod
    def get_user_info(
        self,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get user information."""
        pass
    
    @abstractmethod
    def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ):
        """Update user preferences."""
        pass


class DBUserMemory(UserMemory):
    """Database-backed implementation of UserMemory."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.memory_repo = MemoryRepository(db)

    def store_user_info(
        self,
        user_id: str,
        info: Dict[str, Any],
    ):
        try:
            uid = int(user_id)
        except ValueError:
            return

        user = self.user_repo.get_by_id(uid)
        if not user:
            return

        # 1. Update direct user profile fields if present
        profile_fields = ["age", "gender", "activity_level", "allergies", "conditions"]
        updated_profile = False
        for field in profile_fields:
            if field in info and info[field] is not None:
                val = info[field]
                if isinstance(val, list):
                    if val:  # Only update if the list is not empty
                        val_str = ", ".join([str(item) for item in val if str(item).strip()])
                        if val_str:
                            setattr(user, field, val_str)
                            updated_profile = True
                else:
                    setattr(user, field, val)
                    updated_profile = True
        
        if updated_profile:
            self.user_repo.update(user)

        # 2. Store other facts as memory entries
        source_conversation_id = info.get("source_conversation_id")
        for key, val in info.items():
            if key in profile_fields or key == "source_conversation_id":
                continue
            
            # If val is list, store each item
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str) and item.strip():
                        self.memory_repo.upsert_entry(
                            user_id=uid,
                            entry_type=key,
                            content=item.strip(),
                            source_conversation_id=source_conversation_id
                        )
            elif isinstance(val, str) and val.strip():
                self.memory_repo.upsert_entry(
                    user_id=uid,
                    entry_type=key,
                    content=val.strip(),
                    source_conversation_id=source_conversation_id
                )

    def get_user_info(
        self,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            uid = int(user_id)
        except ValueError:
            return None

        user = self.user_repo.get_by_id(uid)
        if not user:
            return None

        # Gather standard profile fields
        info = {
            "name": user.name,
            "email": user.email,
            "age": user.age,
            "gender": user.gender,
            "activity_level": user.activity_level,
            "allergies": user.allergies,
            "conditions": user.conditions,
        }

        # Gather memory entries
        entries = self.memory_repo.list_by_user(uid)
        facts = {}
        for entry in entries:
            etype = entry.entry_type
            if etype not in facts:
                facts[etype] = []
            facts[etype].append(entry.content)
        
        info["facts"] = facts
        return info

    def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ):
        try:
            uid = int(user_id)
        except ValueError:
            return

        pref = self.db.query(UserPreference).filter(UserPreference.user_id == uid).first()
        if not pref:
            pref = UserPreference(user_id=uid)
            self.db.add(pref)

        if "language" in preferences:
            pref.language = preferences["language"]
        if "response_style" in preferences:
            pref.response_style = preferences["response_style"]
        if "preferred_provider" in preferences:
            pref.preferred_provider = preferences["preferred_provider"]
        if "preferred_model" in preferences:
            pref.preferred_model = preferences["preferred_model"]
        if "extra" in preferences:
            pref.extra_json = preferences["extra"]

        self.db.commit()


class UserMemoryService:
    """Service for user memory operations."""
    
    def __init__(self, memory: UserMemory):
        self.memory = memory
    
    def store(
        self,
        user_id: str,
        info: Dict[str, Any],
    ):
        self.memory.store_user_info(user_id, info)
    
    def get(
        self,
        user_id: str,
    ) -> Optional[Dict[str, Any]]:
        return self.memory.get_user_info(user_id)
