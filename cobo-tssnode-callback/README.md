# cobo-mpc-callback-server-v2-python

## 概述

这是一个TSS节点回调服务器的Python实现。它提供了一个基本模板来处理TSS节点请求，可以根据特定业务需求进行定制。

## 环境要求

- Python 3.10+
- pip

## 部署步骤

### 1. 创建项目环境
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置密钥

将以下密钥文件放置在项目根目录中：

- configs/tss-node-callback-pub.key (TSS节点的RSA公钥)
- configs/callback-server-pri.pem (回调服务器的RSA私钥)

### 4. 启动服务器
```bash
python3 run.py
```

服务器默认将在11020端口启动。


## 测试

### 1. 健康检查

```bash
curl http://127.0.0.1:11020/ping
```

### 2. 集成测试

要与TSS节点测试完整工作流程：

- 确保回调服务器正在运行
- 配置并启动TSS节点
- 通过TSS节点向回调服务器发送请求

有关详细的TSS节点设置，请参考[回调服务器概述](https://www.cobo.com/developers/v2/guides/mpc-wallets/server-co-signer/callback-server-overview)。

## 重要说明

### 基本实现

此模板仅实现基本的服务器结构。
默认允许所有请求。
请根据您的业务需求实现您自己的回调逻辑。


### 依赖项

`extra_info`风险控制参数结构在[cobo-waas2-python-sdk](https://github.com/CoboGlobal/cobo-waas2-python-sdk)中定义
请参考SDK文档了解详细的参数定义。