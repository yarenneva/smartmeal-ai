from typing import Optional, Dict, Any

class User:
    def __init__(self, uid: str, email: str, display_name: Optional[str] = None):
        self.uid = uid
        self.email = email
        self.display_name = display_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uid": self.uid,
            "email": self.email,
            "display_name": self.display_name
        }

    @staticmethod
    def from_dict(source: Dict[str, Any]):
        return User(source["uid"], source["email"], source.get("display_name"))

