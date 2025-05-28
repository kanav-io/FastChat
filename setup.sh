#!/usr/bin/env bash
set -e

# 1. Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment…"
  python3 -m venv venv
fi

# 2. Activate it
# shellcheck source=/dev/null
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

echo
echo "✅ Setup complete!"
echo "Run 'source venv/bin/activate' to activate your environment."
echo "Then use 'python server.py' or 'python client.py --host <HOST> --port <PORT>'."
echo "To exit the environment Run 'deactivate'."
