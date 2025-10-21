import argparse
from dataclasses import dataclass

import yaml

DEFAULT_CONFIG_YAML = "configs/callback-server-config.yaml"


@dataclass
class ServiceConfig:
    service_name: str = "callback-server"
    endpoint: str = "0.0.0.0:11020"
    token_expire_minutes: int = 2
    client_public_key_path: str = "configs/tss-node-callback-pub.key"
    service_private_key_path: str = "configs/callback-server-pri.pem"
    enable_debug: bool = False


def load_yaml_config(config_path: str) -> ServiceConfig:
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f)

        callback_config = yaml_config.get("callback_server", {})
        return ServiceConfig(
            service_name="callback-server",
            endpoint=callback_config.get("endpoint", "0.0.0.0:11020"),
            token_expire_minutes=callback_config.get("token_expire_minutes", 2),
            client_public_key_path=callback_config.get(
                "client_public_key_path", "configs/tss-node-callback-pub.key"
            ),
            service_private_key_path=callback_config.get(
                "service_private_key_path", "configs/callback-server-pri.pem"
            ),
            enable_debug=callback_config.get("enable_debug", False),
        )
    except Exception as e:
        print(f"Failed to load config file {config_path}: {str(e)}")
        print("Using default configuration...")
        return ServiceConfig()


def get_config() -> ServiceConfig:
    """Get configuration from command line args or default"""
    parser = argparse.ArgumentParser(description="Callback Server")
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG_YAML, help="config yaml file path"
    )

    args = parser.parse_args()
    return load_yaml_config(args.config)
