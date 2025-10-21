# Cobo API callback 服务器

通过 Cobo API 处理 callback 消息或 webhook 事件。

## 环境要求

> Python 3.13.5

## 准备

```bash
python3 -m venv .venv

source .venv/bin/activate

pip3 install --upgrade pip

pip3 install -r requirements.txt
```

## 项目配置

复制`.env.example`为`.env`，并填写自己的配置。

## 启动服务

```bash
python3 app.py
```