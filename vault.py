import sys

import hvac
import os
import requests
import logging
import certifi

def get_vault_token(cfg: dict) -> str:
    vault_address = cfg['vault_address']
    username = cfg['vault_username']
    password = os.getenv('VAULT_PASSWORD')
    auth_payload = {
        "password": password
    }
    ca_bundle = certifi.where()
    auth_url = "{}/v1/auth/userpass/login/{}".format(vault_address, username)
    response = requests.post(auth_url, json=auth_payload, verify=ca_bundle)

    if response.status_code == 200:
        logging.info("Connected to vault")
        token = response.json().get("auth", {}).get("client_token", "")
        return token
    else:
        logging.fatal("Authentication failed. Status code: {} and status {}".format(response.status_code, response.json()))
        sys.exit()


def get_vault_secret(cfg: dict, token: str) -> str:
    vault_client = hvac.Client(url=cfg['vault_address'], token=token)
    private_key_response = vault_client.secrets.kv.read_secret_version(path=cfg['vault_secret_path'], mount_point=cfg['vault_mount_point'])
    private_key = private_key_response['data']['data'][cfg['vault_key']]
    return private_key


def get_privkey_from_vault(cfg: dict) -> str:
    token = get_vault_token(cfg)
    return get_vault_secret(cfg, token)
