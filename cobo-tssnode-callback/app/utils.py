import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_keys(public_key_path, private_key_path):
    try:
        with open(public_key_path, "rb") as pub_file:
            public_key_content = pub_file.read()

        with open(private_key_path, "rb") as priv_file:
            private_key_content = priv_file.read()

        return public_key_content, private_key_content
    except Exception as e:
        logger.error(f"Failed to load keys: {str(e)}")
        raise
