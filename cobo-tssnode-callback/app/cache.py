import pika
import json
import logging
import time
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost"),
)
channel = connection.channel()
channel.queue_declare(queue="cobo")

global_message_cache = {}

# 消息过期时间（秒）
MESSAGE_TTL = 30


def callback(ch, method, properties, body):
    json_str = body.decode()
    logger.debug(f"Received message: {json_str}")
    msg = json.loads(json_str)

    # 清理过期消息
    cleanup_expired_messages()

    # 存储消息并记录当前时间
    global_message_cache[msg["transaction_id"]] = {
        "data": msg,
        "timestamp": time.time()
    }


def cleanup_expired_messages():
    """清理过期消息"""
    current_time = time.time()
    expired_keys = []

    # 找出过期的消息
    for key, value in global_message_cache.items():
        if current_time - value["timestamp"] > MESSAGE_TTL:
            expired_keys.append(key)

    # 删除过期消息
    for key in expired_keys:
        del global_message_cache[key]
        logger.warning(f"Removed expired message with transaction_id: {key}")

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired messages")


def get_transaction(transaction_id):
    """获取缓存的消息"""
    entry = global_message_cache.get(transaction_id)
    if entry:
        # 检查消息是否过期
        if time.time() - entry["timestamp"] <= MESSAGE_TTL:
            data = entry["data"]
            del global_message_cache[transaction_id]
            return data
    return None


def get_cache_size():
    """获取当前缓存大小"""
    return len(global_message_cache)


# 导出函数
__all__ = ['get_transaction']

channel.basic_consume(
    queue="cobo", on_message_callback=callback, auto_ack=True)


def start_cache_consumer():
    """启动消息消费者线程"""
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Message consuming stopped")
        channel.stop_consuming()
        connection.close()

consumer_thread = threading.Thread(target=start_cache_consumer, daemon=True)
consumer_thread.start()