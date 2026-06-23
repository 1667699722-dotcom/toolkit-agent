cd /Users/liuhuachao/Documents/trae_projects/internet
source venv/bin/activate
export API_KEY="$(cat "$HOME/Desktop/deepseek.xml")"
export BASE_URL="https://api.deepseek.com/v1"
export MODEL="deepseek-chat"
python3 toolkit_agent.py


