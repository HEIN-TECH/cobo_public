import hashlib
import json
import logging
import pika
from typing import Optional
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from cobo_waas2 import WebhookEvent, Transaction
import dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载 .env 配置文件
dotenv.load_dotenv()
allow_list_str = dotenv.get_key(".env", "IP_ALLOWLIST")
allow_list = [ip.strip() for ip in allow_list_str.split(",")] if allow_list_str else ["127.0.0.1"]
if "127.0.0.1" not in allow_list:
    allow_list.append("127.0.0.1")

logger.info(f"IP allow list: {allow_list}")

# 加载RabbitMQ
def init_rabbitmq():
    global connection, mq_channel
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost"),
    )
    mq_channel = connection.channel()
    mq_channel.queue_declare(queue="cobo")

init_rabbitmq()

# 启动服务器
app = FastAPI()


# Select the public key based on the environment that you use,
# DEV for the development environment and PROD for the production environment.
pub_keys = {
    "DEV": "a04ea1d5fa8da71f1dcfccf972b9c4eba0a2d8aba1f6da26f49977b08a0d2718",
    "PROD": "8d4a482641adb2a34b726f05827dba9a9653e5857469b8749052bf4458a86729",
}

pubkey = pub_keys["DEV"]


@app.post("/api/webhook")
async def handle_webhook(
    request: Request,
    biz_timestamp: Optional[str] = Header(None),
    biz_resp_signature: Optional[str] = Header(None),
):
    raw_body = await request.body()
    sig_valid = verify_signature(
        pubkey, biz_resp_signature, f"{raw_body.decode('utf8')}|{biz_timestamp}"
    )
    if not sig_valid:
        raise HTTPException(
            status_code=401, detail="Signature verification failed")
    event = WebhookEvent.from_dict(json.loads(raw_body.decode('utf8')))
    logger.info(event)
    logger.info(event.data)


@app.post("/api/callback", response_class=PlainTextResponse)
async def handle_callback(
    request: Request,
    biz_timestamp: Optional[str] = Header(None),
    biz_resp_signature: Optional[str] = Header(None),
):
    raw_body = await request.body()
    sig_valid = verify_signature(
        pubkey, biz_resp_signature, f"{raw_body.decode('utf8')}|{biz_timestamp}"
    )
    tx = Transaction.from_dict(json.loads(raw_body.decode('utf8')))
    logger.info(tx)
    if not sig_valid:
        raise HTTPException(
            status_code=401, detail="Signature verification failed")

    # 验证发起方IP
    # from_ip = request.client.host  # 请求发起方的IP
    # if from_ip not in allow_list:
    #     raise HTTPException(
    #         status_code=403, detail=f"IP {from_ip} is not allowed")

    # TODO 添加实际的 API 请求验证逻辑，目前无条件通过

    # 把 tx 信息发送到 TSS Node callback 进程以备验证
    msg = {
        "transaction_id": tx.transaction_id,
        "wallet_id": tx.wallet_id,
        "chain_id": tx.chain_id,
        "created_timestamp": tx.created_timestamp,
    }
    
    # 检查RabbitMQ连接状态
    if mq_channel.is_open:
        mq_channel.basic_publish(exchange="", routing_key="cobo",
                                 body=json.dumps(msg))
    else:
        logger.warning("RabbitMQ channel is not open. Attempting to reconnect...")
        try:
            init_rabbitmq()
            
            # 重新连接后再次尝试发送消息
            mq_channel.basic_publish(exchange="", routing_key="cobo",
                                     body=json.dumps(msg))
            logger.info("Successfully reconnected to RabbitMQ and sent message.")
        except Exception as e:
            logger.error(f"Failed to reconnect to RabbitMQ: {e}")
            return "deny"

    return "ok"


def verify_signature(public_key, signature, message):
    vk = VerifyKey(key=bytes.fromhex(public_key))
    sha256_hash = hashlib.sha256(hashlib.sha256(
        message.encode()).digest()).digest()
    try:
        vk.verify(signature=bytes.fromhex(signature), smessage=sha256_hash)
        return True
    except BadSignatureError:
        return False


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
