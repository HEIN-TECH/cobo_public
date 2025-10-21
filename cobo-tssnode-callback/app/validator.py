from cobo_waas2 import TSSKeySignRequest, TSSKeySignExtra
import logging
from eth_utils import keccak
import dotenv
from app.cache import get_transaction

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/validator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

EVM_ID = dotenv.get_key(".env", "EVM_CHAINS")
EVM_ID = [chain.strip() for chain in EVM_ID.split(",")
          ] if EVM_ID else []
SOLANA_ID = dotenv.get_key(".env", "SOLANA_CHAINS")
SOLANA_ID = [chain.strip() for chain in SOLANA_ID.split(",")
             ] if SOLANA_ID else []


def validate_key_sign(detail: TSSKeySignRequest, extra: TSSKeySignExtra):
    # 验证交易哈希以防止交易被篡改
    chain = extra.transaction.chain_id
    raw_tx = extra.transaction.raw_tx_info.unsigned_raw_tx
    msg_hash = detail.msg_hash_list[0]
    if chain in EVM_ID:
        print("EVM transaction verify")
        evm_transaction_verify(raw_tx, msg_hash)
    elif chain in SOLANA_ID:
        solana_transaction_verify(raw_tx, msg_hash)
    else:
        logger.warning(f"Unsupported chain: {chain}")
        raise Exception(f"Unsupported chain: {chain}")

    # 根据 API callback 获取到的 tx 数据和此处
    # extra.transaction.raw_tx_info.unsigned_raw_tx 解析出的交易数
    # 据进行对比，验证交易的有效性

    tx_id = extra.transaction.transaction_id
    tx = get_transaction(tx_id)
    if not tx:
        logger.error(f"Transaction {tx_id} not found in cache")
        raise Exception(f"Transaction {tx_id} not found in cache")
    wallet_id = tx["wallet_id"]
    if extra.transaction.wallet_id != wallet_id:
        raise Exception(f"Wallet ID {wallet_id} mismatch source {extra.transaction.wallet_id}")
    chain_id = tx["chain_id"]
    if extra.transaction.chain_id != chain_id:
        raise Exception(f"Chain ID {chain_id} mismatch source {extra.transaction.chain_id}")
    created_timestamp = tx["created_timestamp"]
    if extra.transaction.created_timestamp != created_timestamp:
        raise Exception(f"Created timestamp {created_timestamp} mismatch source {extra.transaction.created_timestamp}")
    return


def evm_transaction_verify(raw_tx: str, msg_hash: str):
    '''
    验证 EVM 原始交易的有效性，使用 Keccak-256 算法
    '''
    hex_bytes = bytes.fromhex(raw_tx)
    hash_result = "0x" + keccak(hex_bytes).hex()
    print(hash_result)
    print(msg_hash)
    if hash_result == msg_hash:
        return
    else:
        logger.warning(f"Message hash: {msg_hash} does not match hash result: {hash_result}")
        raise Exception("EVM transaction verify failed")


def solana_transaction_verify(raw_tx: str, msg_hash: str):
    '''
    TODO 验证 Solana 原始交易有效性 
    '''
    # raise NotImplementedError("还没有实现Solana交易验证")
    # 目前无条件通过Solana交易
    return
