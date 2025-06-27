# 💬 FastChat: Terminal-Based End-to-End Encrypted Chat Server

**FastChat** is a powerful, terminal-based chat application built with Python, delivering modern **end-to-end encryption**, secure **user authentication**, and efficient **file and message handling**. With robust cryptography, multi-client support, and MongoDB-backed persistence, FastChat is designed for security and usability.

---

## 🚀 Features

### ✅ Authentication & User Management

* **Secure Registration & Login** with Argon2id password hashing (salt + pepper)
* **Local Private Key Storage:** 
  - Private keys saved at `~/.fastchat/<user>/private_key.bin`
  - Public keys (Base64) stored in MongoDB
* **Username uniqueness** enforced at registration

### 🔐 End-to-End Encryption

* **X25519 Diffie–Hellman handshake** for establishing session keys
* **Signal-style Double Ratchet** protocol for forward secrecy and message confidentiality
* **Private messaging** via `@username <message>` – server forwards ciphertext only

### 🗂️ Message & File Storage

* **Encrypted message persistence** in MongoDB (payloads, timestamps, sender/recipient)
* **Encrypted file transfer** with `/sendfile <user> <path>`:
  - Chunked in 4 KiB blocks
  - Terminal progress bar for transfer status

### 👥 Group & Private Chat

* **Global broadcast chat**: send messages to all connected users
* **Private messaging**: direct and secure user-to-user communication
* **/who command**: list all currently online users

### 🧑‍💻 Server & Administration

* **Multi-client concurrency** using Python threading
* **Admin console commands**:
  - `/getClient` — list connected clients
  - `/terminate` — gracefully shut down server
  - `/clear` — clear chat/session data

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
* Ensure necessary databases are initialized

```bash
chmod +x setup.sh
./setup.sh
```
> 💡 If you're on Windows, run the equivalent commands manually or adapt `setup.sh` using `.bat` or PowerShell.

### 3. Start MongoDB

You need a running MongoDB instance for FastChat to work.  
**On Mac (using Homebrew):**

```bash
brew services start mongodb-community
```
> 💡 Make sure MongoDB is running before starting the server or client.

### 4. Activate the Environment (if not already activated)

```bash
source venv/bin/activate
```

### 5. Start the Server

```bash
python server.py
```

### 6. Start the Client

In a separate terminal (after activating the environment):

```bash
python client.py
```

---

## 🧪 Example Commands

* Register: `/register user strongpass`
* Login: `/login user strongpass`
* Private Message: `@user Hello!`
* Send File: `/sendfile user /path/to/file`
* Show Users Online: `/who`
* Exit: `/exit`

---

## 🧰 Tech Stack

* Python 3.13 (`socket`, `threading`, `os`)
* PyNaCl for cryptographic operations (X25519, Double Ratchet)
* argon2-cffi for Argon2id password hashing
* pymongo for MongoDB integration
* tqdm for terminal progress bars
* Git for version control (hosted on GitHub)

---

## 📌 To-Do / Future Work

* ⏳ Multi-room/group chat support
* ⏳ Enhanced user status (online/away/busy)
* ⏳ GUI front-end (Tkinter or PyQt)
* ⏳ Message search and filtering
* ⏳ Advanced admin tools

---

## 🧠 Why This Project Matters

This project demonstrates:

* Building a **secure, encrypted messaging platform** from scratch
* Implementation of **modern cryptographic protocols** (X25519, Double Ratchet)
* Real-world experience in **network programming**, **client-server architecture**, and **concurrent systems**
* Integration of **secure authentication** and **scalable data persistence**

---

## 📝 License

Apache License 2.0. See `LICENSE` file.

---
