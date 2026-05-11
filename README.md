## PyChat

A terminal-based chat app written in Python. Users can register with a unique code (like alice#4231), chat in a global room, create private servers, send direct messages, and manage a friends list.

## Features

User registration and login with hashed passwords
Discord-style user codes (username#NNNN) to avoid duplicate names
Global chat with basic moderation (ban, mute, promote)
Private servers with password protection and per-server roles
Direct messaging between users
Friend requests and friend list

## Setup

No additional setup needed — the database is created automatically on first run.

## Technologies
- Python
- SQLite

## Project structure
src/
  auth.py      # registration, login, password hashing
  db.py        # all database access (SQLite)
  models.py    # User class
  main.py      # CLI entry point and menus
Notes
Passwords are stored as SHA-256 hashes. The app runs fully in the terminal — no web interface.