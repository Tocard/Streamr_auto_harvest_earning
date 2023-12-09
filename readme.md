# Auto Collect Earning For Streamr Operator

## Requierements


````shell
pip install -r requierements.txt
````

## Warning Security attention

This script provide two method to get privkey. One from yaml file wich is not encouraged, use it only if you have any other solution.

The best way is to use hashicorp vault and fetch method with VAULT_CREDENTIAL set as env services which is pretected by default. 

If you don't know how to install it checkout my ansible collection https://github.com/Tocard/ansible_collection for automatisation. Otherwiwe product documentation https://developer.hashicorp.com/vault/docs/install 

Other concern about security, use a third wallet to run earning command. If this one is compromised beacause of third library ike web3, your operator will stay safe

## Usage

python main.py --config_path config.yml

