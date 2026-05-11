import hashlib
import re

from db import create_user, get_user_by_id, user_code_exists

ALLOWED_COLORS = ["red", "green", "blue", "yellow", "purple", "cyan"]


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def is_valid_username(username):
    # at least 4 chars, only letters, numbers and underscores
    return bool(re.match(r"^\w{4,}$", username))


def is_valid_password(password):
    return len(password) >= 8


def pick_color():
    while True:
        color = input(f"Choose a color ({'/'.join(ALLOWED_COLORS)}): ").strip().lower()
        if color in ALLOWED_COLORS:
            return color
        print(f"Please choose one of: {', '.join(ALLOWED_COLORS)}")


def register_user(user_id, username, password, profile_pic=None, color=None, role="user"):
    if not is_valid_username(username):
        return False, "Username must be at least 4 characters (letters, numbers, underscores only)."

    if not is_valid_password(password):
        return False, "Password must be at least 8 characters."

    if color is None:
        color = pick_color()
    elif color not in ALLOWED_COLORS:
        return False, f"Color must be one of: {', '.join(ALLOWED_COLORS)}"

    hashed = hash_password(password)

    if create_user(user_id, username, hashed, profile_pic, color, role):
        return True, f"Account created! Your user code is: {user_id}"

    return False, "Something went wrong. Username might already exist."


def login_user(user_id, password):
    # user_id is the full code like "bob#1234"
    user = get_user_by_id(user_id)
    if user and user["password"] == hash_password(password):
        return True, user
    return False, None