class User:
    """Represents a registered user."""

    def __init__(self, user_id, username, profile_pic=None, color="red", role="user"):
        self.user_id = user_id      # full code like "alice#4231"
        self.username = username
        self.profile_pic = profile_pic
        self.color = color
        self.role = role

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_mod(self):
        return self.role in ("admin", "mod")

    @classmethod
    def from_db_row(cls, row):
        """Create a User from a database row dict."""
        return cls(
            user_id=row["id"],
            username=row["username"],
            profile_pic=row.get("profile_pic"),
            color=row.get("color", "red"),
            role=row.get("role", "user"),
        )

    def __repr__(self):
        return f"User(id={self.user_id!r}, role={self.role!r})"