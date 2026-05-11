# ACHTUNG: Ab jetzt bekommt jeder neue User beim Registrieren einen zufälligen vierstelligen Code (wie Discord: z.B. bob#1234).
# Die alte Registrierung ist unten auskommentiert, damit man sieht, wie es vorher war.
# Das macht es leichter, User zu finden und Freundschaftsanfragen zu verschicken.

import getpass
import random

from auth import register_user, login_user, ALLOWED_COLORS, pick_color
from db import (
    init_db,
    create_messages_table,
    create_moderation_tables,
    create_servers_table,
    create_private_messages_table,
    create_friends_table,
    create_server_moderation_tables,
    save_message,
    get_last_messages,
    ban_user,
    is_banned,
    mute_user,
    is_muted,
    unban_user,
    unmute_user,
    set_user_role,
    get_all_users,
    create_server,
    get_servers_for_user,
    join_server,
    leave_server,
    delete_server,
    get_server_by_name,
    get_server_by_id,
    get_server_members,
    set_server_member_role,
    save_server_message,
    get_server_messages,
    count_user_servers,
    update_server_password,
    get_user_by_username,
    get_username_by_id,
    save_private_message,
    get_private_messages_for_user,
    send_friend_request,
    accept_friend_request,
    remove_friend,
    get_friends,
    get_pending_friend_requests,
    user_code_exists,  # <- NEU: Prüft, ob username#code schon existiert
)

CURSE_WORDS = ["idiot", "slut", "fuck", "shit", "bitch"]

ROLE_COLORS = {
    "owner": "\033[91m",
    "admin": "\033[92m",
    "mod":   "\033[95m",
}
RESET = "\033[0m"

def generate_user_code():
    return "{:04d}".format(random.randint(0, 9999))

def censor_message(msg):
    words = msg.split()
    for i, word in enumerate(words):
        for curse in CURSE_WORDS:
            if curse.lower() in word.lower():
                words[i] = "*" * len(word)
                break
    return " ".join(words)

def get_role_color(role):
    return ROLE_COLORS.get(role, RESET)

def friends_interface(user):
    while True:
        print("\n-- Friends Menu --")
        print("1. Show my friends")
        print("2. Show pending requests")
        print("3. Send friend request")
        print("4. Remove friend")
        print("5. Back")
        choice = input("> ").strip()
        if choice == "1":
            friends = get_friends(user["id"])
            if not friends:
                print("  You have no friends yet.")
            else:
                print("  Your friends:")
                for f in friends:
                    print(f"   - {f}")
        elif choice == "2":
            requests = get_pending_friend_requests(user["id"])
            if not requests:
                print("  No pending requests.")
            else:
                print("  Pending requests:")
                for req in requests:
                    print(f"   - {req}")
                accept = input("  Accept one? Enter user code or leave empty: ").strip()
                if accept:
                    accept_friend_request(accept, user["id"])
                    print(f"  Accepted {accept}.")
        elif choice == "3":
            target = input("  Enter user code to add (e.g. bob#1234): ").strip()
            if target == user["id"]:
                print("  You can't add yourself.")
            else:
                send_friend_request(user["id"], target)
                print(f"  Friend request sent to {target}.")
        elif choice == "4":
            target = input("  Enter user code to remove: ").strip()
            remove_friend(user["id"], target)
            print(f"  Removed {target} from your friends.")
        elif choice == "5":
            break
        else:
            print("  Invalid choice.")

def chat_interface(username, role):
    print("\n-- Global Chat --")
    print("Type /help to see commands or /back to exit.\n")
    while True:
        if is_banned(username):
            print("You have been banned.")
            break
        print("\nLast messages:")
        messages = get_last_messages()
        if messages:
            for user, msg, ts in messages:
                print(f"  [{ts}] {user}: {msg}")
        else:
            print("  No messages yet.")
        raw = input("\n> ").strip()
        if raw == "/back":
            break
        elif raw == "/help":
            print("\nCommands:")
            print("  /back          - return to menu")
            print("  /myid          - show your user code")
            if role in ("admin", "mod"):
                print("  /users         - list all users")
                print("  /ban <user>    - ban a user")
                print("  /unban <user>  - unban a user")
                print("  /mute <user>   - mute a user")
                print("  /unmute <user> - unmute a user")
            if role == "admin":
                print("  /promote <user> <role> - change role (admin/mod/user)")
                print("  /demote <user>         - set role back to user")
        elif raw == "/myid":
            user = get_user_by_username(username)
            if user:
                print(f"  Your code: {user['id']}")
        elif raw == "/users" and role in ("admin", "mod"):
            for u, r in get_all_users():
                print(f"  {u} ({r})")
        elif raw.startswith("/ban ") and role in ("admin", "mod"):
            target = raw.split(" ", 1)[1].strip()
            ban_user(target)
            print(f"  {target} has been banned.")
        elif raw.startswith("/unban ") and role in ("admin", "mod"):
            target = raw.split(" ", 1)[1].strip()
            unban_user(target)
            print(f"  {target} has been unbanned.")
        elif raw.startswith("/mute ") and role in ("admin", "mod"):
            target = raw.split(" ", 1)[1].strip()
            mute_user(target)
            print(f"  {target} has been muted.")
        elif raw.startswith("/unmute ") and role in ("admin", "mod"):
            target = raw.split(" ", 1)[1].strip()
            unmute_user(target)
            print(f"  {target} has been unmuted.")
        elif raw.startswith("/promote ") and role == "admin":
            parts = raw.split()
            if len(parts) == 3:
                target, new_role = parts[1], parts[2]
                if new_role in ("admin", "mod", "user"):
                    set_user_role(target, new_role)
                    print(f"  {target} is now {new_role}.")
                else:
                    print("  Role must be admin, mod or user.")
            else:
                print("  Usage: /promote <username> <role>")
        elif raw.startswith("/demote ") and role == "admin":
            parts = raw.split()
            if len(parts) == 2:
                set_user_role(parts[1], "user")
                print(f"  {parts[1]} demoted to user.")
            else:
                print("  Usage: /demote <username>")
        elif raw:
            if is_muted(username):
                print("  You are muted.")
            else:
                save_message(username, censor_message(raw))

def server_chat_interface(username, server_id, user_role):
    while True:
        messages = get_server_messages(server_id)
        members = dict(get_server_members(server_id))
        server = get_server_by_id(server_id)
        if not server:
            print("This server no longer exists.")
            break
        print(f"\n-- {server['name']} ({len(members)} members) --")
        if messages:
            for user, msg, ts in messages:
                color = get_role_color(members.get(user, "user"))
                print(f"  {color}[{ts}] {user}: {msg}{RESET}")
        else:
            print("  No messages yet.")
        print("\nType /help for commands or /back to exit.")
        raw = input("\n> ").strip()
        if raw == "/back":
            break
        elif raw == "/help":
            print("\nCommands:")
            print("  /back          - return to server list")
            print("  /myid          - show your user code")
            print("  /users         - list all members")
            print("  /leave         - leave this server")
            if user_role == "owner":
                print("  /kick <user>               - kick a member")
                print("  /ban <user>                - ban a member")
                print("  /mute <user>               - mute a member")
                print("  /promote <user> <role>     - change member role")
                print("  /demote <user>             - reset role to user")
                print("  /setpassword               - set server password")
                print("  /removepassword            - remove server password")
                print("  /delete                    - delete this server")
        elif raw == "/myid":
            user = get_user_by_username(username)
            if user:
                print(f"  Your code: {user['id']}")
        elif raw == "/users":
            print(f"\n  Members of {server['name']}:")
            for u, r in get_server_members(server_id):
                print(f"    {u} ({r})")
        elif raw == "/leave":
            leave_server(server_id, username)
            print("You left the server.")
            break
        elif raw == "/delete" and user_role == "owner":
            confirm = input("  Are you sure? (yes/no): ").strip().lower()
            if confirm == "yes":
                delete_server(server_id)
                print("Server deleted.")
                break
        elif raw.startswith("/kick ") and user_role == "owner":
            target = raw.split(" ", 1)[1].strip()
            if target == username:
                print("  You can't kick yourself.")
            else:
                leave_server(server_id, target)
                print(f"  {target} was kicked.")
        elif raw.startswith("/ban ") and user_role == "owner":
            target = raw.split(" ", 1)[1].strip()
            ban_user(target)
            print(f"  {target} was banned.")
        elif raw.startswith("/mute ") and user_role == "owner":
            target = raw.split(" ", 1)[1].strip()
            mute_user(target)
            print(f"  {target} was muted.")
        elif raw.startswith("/promote ") and user_role == "owner":
            parts = raw.split()
            if len(parts) == 3:
                target, new_role = parts[1], parts[2]
                if new_role in ("admin", "mod", "user"):
                    set_server_member_role(server_id, target, new_role)
                    print(f"  {target} is now {new_role}.")
                else:
                    print("  Role must be admin, mod or user.")
            else:
                print("  Usage: /promote <username> <role>")
        elif raw.startswith("/demote ") and user_role == "owner":
            parts = raw.split()
            if len(parts) == 2:
                set_server_member_role(server_id, parts[1], "user")
                print(f"  {parts[1]} demoted to user.")
            else:
                print("  Usage: /demote <username>")
        elif raw == "/setpassword" and user_role == "owner":
            new_pass = getpass.getpass("  New password (leave empty to remove): ")
            update_server_password(server_id, new_pass if new_pass else None)
            print("  Password updated.")
        elif raw == "/removepassword" and user_role == "owner":
            update_server_password(server_id, None)
            print("  Password removed.")
        elif raw:
            if is_muted(username):
                print("  You are muted.")
            else:
                save_server_message(server_id, username, raw)

def private_messages_interface(user):
    while True:
        print("\n-- Private Messages --")
        print("1. View messages")
        print("2. Send a message")
        print("3. Back")
        choice = input("> ").strip()
        if choice == "1":
            messages = get_private_messages_for_user(user["id"])
            if not messages:
                print("  No messages yet.")
            else:
                for sender, receiver, msg, ts in messages:
                    if sender == user["id"]:
                        print(f"  [{ts}] To {receiver}: {msg}")
                    else:
                        print(f"  [{ts}] From {sender}: {msg}")
        elif choice == "2":
            receiver_id = input("  Recipient user code (e.g. bob#1234): ").strip()
            receiver_name = get_username_by_id(receiver_id)
            if not receiver_name:
                print("  No user found with that code.")
                continue
            msg = input(f"  Message to {receiver_name}: ").strip()
            if msg:
                save_private_message(user["id"], receiver_id, msg)
                print("  Sent.")
        elif choice == "3":
            break
        else:
            print("  Invalid choice.")

def main():
    # Initialisiere alle Tabellen beim Start
    init_db()
    create_messages_table()
    create_moderation_tables()
    create_servers_table()
    create_private_messages_table()
    create_friends_table()
    create_server_moderation_tables()

    print("\nWelcome to PyChat!")

    while True:
        print("\n-- Menu --")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("> ").strip()
        if choice == "1":
            username = input("  Username: ").strip()
            password = getpass.getpass("  Password: ")
            color = pick_color()
            role = "admin" if username == "admin" else "user"
            # NEU: Generiere einen zufälligen vierstelligen Code und prüfe, ob die Kombination schon existiert
            while True:
                code = generate_user_code()
                if not user_code_exists(username, code):
                    break
            user_id = f"{username}#{code}"
            # Die register_user Funktion muss jetzt user_id als ersten Parameter nehmen!
            success, message = register_user(user_id, username, password, None, color, role)
            if success:
                print(f"  Registration successful! Your user code: {user_id}")
            else:
                print(f"  {message}")

            # ALT (auskommentiert):
            # success, message = register_user(username, password, None, color, role)
            # print(f"  {message}")

        elif choice == "2":
            user_id = input("  Your user code (e.g. bob#1234): ").strip()
            password = getpass.getpass("  Password: ")
            success, user = login_user(user_id, password)
            if not success:
                print("  Login failed. Check your credentials.")
                continue
            # Hauptmenü nach Login
            while True:
                print(f"\nWelcome, {user['username']} ({user['role']})")
                print(f"Your code: {user['id']}")
                print("\n1. Global Chat")
                print("2. My Servers")
                print("3. Join a Server")
                print("4. Create a Server")
                print("5. Private Messages")
                print("6. Friends")
                print("7. Logout")
                sub = input("> ").strip()
                if sub == "1":
                    chat_interface(user["username"], user["role"])
                elif sub == "2":
                    servers = get_servers_for_user(user["username"])
                    if not servers:
                        print("  You are not in any server yet.")
                        answer = input("  Create one? (yes/no): ").strip().lower()
                        if answer == "yes":
                            sub = "4"
                        else:
                            continue
                    if sub == "2":
                        print("\n  Your servers:")
                        for idx, (sid, sname, srole) in enumerate(servers, 1):
                            print(f"  {idx}. {sname} (role: {srole})")
                        pick = input("  Enter number to open (or Enter to cancel): ").strip()
                        if pick.isdigit() and 1 <= int(pick) <= len(servers):
                            sid, sname, srole = servers[int(pick) - 1]
                            server_chat_interface(user["username"], sid, srole)
                        elif pick:
                            print("  Invalid selection.")
                elif sub == "3":
                    sname = input("  Server name: ").strip()
                    server = get_server_by_name(sname)
                    if not server:
                        print("  Server not found.")
                        continue
                    if server["password"]:
                        entered = getpass.getpass("  Server password: ")
                        if entered != server["password"]:
                            print("  Wrong password.")
                            continue
                    user_code = input("  Your user code: ").strip()
                    username_to_add = get_username_by_id(user_code)
                    if not username_to_add:
                        print("  Invalid user code.")
                        continue
                    join_server(server["id"], username_to_add)
                    print(f"  Joined '{sname}'!")
                elif sub == "4":
                    if count_user_servers(user["username"]) >= 2:
                        print("  You can only own up to 2 servers.")
                    else:
                        sname = input("  Server name: ").strip()
                        if not sname:
                            print("  Name can't be empty.")
                        elif get_server_by_name(sname):
                            print("  That name is already taken.")
                        else:
                            pw = getpass.getpass("  Password (leave empty for public): ")
                            sid = create_server(sname, user["username"], pw if pw else None)
                            print(f"  Server '{sname}' created! You are the owner.")
                elif sub == "5":
                    private_messages_interface(user)
                elif sub == "6":
                    friends_interface(user)
                elif sub == "7":
                    print(f"  Goodbye, {user['username']}!")
                    break

if __name__ == "__main__":
    main()