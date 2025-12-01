**For Windows users:** MCP servers have compatibility issues on Windows. We use WSL (Windows Subsystem for Linux) to run MCP code in a Linux environment where it works properly.

**Here are all the steps to run MCP code in WSL:**

## 1. Install WSL (if not already done)
```powershell
# In PowerShell as Administrator (Windows)
wsl --install
# Restart computer
```

## 2. Open WSL
- Open "Ubuntu" from Start Menu, or type `wsl` in terminal

### Verify Python installation

Most WSL Ubuntu installations come with Python pre-installed. Verify it's available by running:

```bash
python3 --version
```

If Python is not installed, install it with:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

## 3. Install uv (Python package manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Make it permanent
echo 'source $HOME/.cargo/env' >> ~/.bashrc
```

## 4. Install Node.js (for MCP servers)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
```

## 5. Navigate to your project
1. Open Cursor IDE
2. Open the terminal panel
3. In the terminal dropdown, select **WSL** from the list of available terminals
4. The path to your project directory should be displayed
```bash
cd /mnt/d/workspace/full_path_here/agentverse
```

## 6. Clean up Windows .venv and create fresh one
```bash
rm -rf .venv
uv venv
```

## 7. Sync dependencies
```bash
uv sync
```

## 8. Start Jupyter Lab
```bash
uv run jupyter lab
```
Copy the URL from terminal (like `http://localhost:8888/...`) and paste into your Windows browser

**Now you can run your MCP code in the notebook!**



---
📢 Discover more Agentic AI notebooks on my [GitHub repository](https://github.com/lisekarimi/agentverse) and explore additional AI projects on my [portfolio](https://lisekarimi.com).
