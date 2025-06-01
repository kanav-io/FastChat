# 💬 FastChat: Terminal-Based Encrypted Chat Server

**FastChat** is a lightweight, terminal-based chat application built with Python, offering secure **user authentication**, **private messaging**, and **message history logging** using `SQLite` and `bcrypt`. Ideal for small-scale secure internal communication.

---

## 🚀 Features

### ✅ Authentication & User Management

* **Secure Registration** with salted `bcrypt` password hashing
* **Login system** with verification against stored hashes
* **Username uniqueness** enforced via SQLite constraints

### 🗂️ Message Storage

* All messages are persistently stored in **SQLite databases**:

  * `chat_users.db` for credentials
  * `chat_history.db` for messages
* Automatically creates the required tables on first run

### 👥 Group Chat

* Global chat broadcasting to all connected users
* Displays the **last 10 messages** on successful login

### 🧑‍💻 Private Messaging

* Send **direct messages** to specific users using:

  ```
  @username your private message
  ```
* Bi-directional confirmation of private messages
* Notifies when the target user is **offline or unavailable**

### 📡 Real-Time Server

* Asynchronous multi-client handling via Python `threading`
* Admin console with support for the `$terminate` command to shut down the server cleanly

### 🔍 Online User Discovery

* Built-in `/who` command to list all currently connected usernames


---

## 🛠️ Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/kanav-io/FastChat.git
cd FastChat
```

### 2. Run the Setup Script

This will:

* Create and activate a virtual environment
* Install all dependencies from `requirements.txt`
* Make sure necessary databases are initialized

```bash
chmod +x setup.sh
./setup.sh
```

> 💡 If you're on Windows, run the equivalent commands manually or adapt `setup.sh` using `.bat` or PowerShell.

### 3. Activate the Environment (if not already activated)

```bash
source venv/bin/activate
```

### 4. Run the Server

```bash
python server.py
```

---

---

## 🧪 Example Commands

* Register: `$register user strongpass`
* Login: `$login user strongpass`
* Private Message: `@user Hey there!`
* Show Users Online: `/who`
* Exit: `$exit`

---

## 🧰 Tech Stack

* Python 3.13
* `socket`, `threading`, `os`
* `bcrypt` for password hashing
* `sqlite3` for data storage
* Terminal-based interface

---

## 📌 To-Do / Future Work

* ✅ Encrypted message storage
* ✅ Private direct messaging
* ⏳ File transfer support
* ⏳ User status (online/away)
* ⏳ GUI front-end (Tkinter or PyQt)
* ⏳ Multi-room support / Group creation
* ⏳ End-to-end encryption (E2EE)

---

## 🧠 Why This Project Matters

This project simulates building a **fully functional backend system** for a messaging platform. It demonstrates:

* Strong understanding of **network programming**
* Use of **secure authentication** practices
* Real-world experience in **client-server architecture**

---

## 📝 License

Apache License 2.0. See `LICENSE` file.

---
