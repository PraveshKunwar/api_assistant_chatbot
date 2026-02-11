# 💬 Chatbot template

A simple Streamlit app that shows how to build a chatbot using OpenAI's GPT-3.5.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements
```bash
pip install -r requirements.txt
```

2. Set .env according to template .env.sample
Regarding ACCESS_TOKEN, we need to retrieve this from the maizey project page. A past token will need to be revoked before getting a new one, and the expiration duration is typically one year.
```bash
source .env
```


3. Run the app
```bash
streamlit run streamlit_app.py
```
### For Deployment
This app currently uses the old maizey project from Summer 2025, with need of token renewal each year and potential owner removal.
Before running the script, we need to set maizey-secret on openshift similar to .env.

UI instruction:
1. Go to secrets tab at openshift
2. Select Key/Value Pair
3. Enter PROJECT_PK and ACCESS_TOKEN

TODO:
Local Script Instruction

To deploy:
```shell
# Login via web from local terminal
oc login --web --server=https://api.containersprod.art2.p1.openshiftapps.com:6443
oc project apidir-dev
chmod +x install.sh
./install.sh
```

To undeploy:
```shell
chmod +x uninstall.sh
./uninstall.sh
```