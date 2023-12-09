# Auto Collect Earning For Streamr Operator

## Requierements

### Linux Pattern foldering 

This step is optionnal, but you should consider about using it for any application you're running.

````shell
cd /opt
git clone https://github.com/Tocard/Streamr_auto_harvest_earning.git 
mkdir /var/log/Streamr_auto_harvest_earning
touch /var/log/Streamr_auto_harvest_earning/harvesting.log
chmod +x Streamr_auto_harvest_earning/run_harvest.sh
````


### Python
````shell
python -m venv .
source bin/activate
pip install -r requierements.txt
````

## Warning Security attention

This script provide two method to get privkey. One from yaml file wich is not encouraged, use it only if you have any other solution.

The best way is to use hashicorp vault and fetch method with VAULT_CREDENTIAL set as env services which is pretected by default. 

If you don't know how to install it checkout my ansible collection https://github.com/Tocard/ansible_collection for automatisation. Otherwiwe product documentation https://developer.hashicorp.com/vault/docs/install 

Other concern about security, use a third wallet to run earning command. If this one is compromised beacause of third library ike web3, your operator will stay safe

Please, never run anything under root privilege. This is a big issue and could have huge consequences.

## Usage
````shell
python main.py --config_path config.yml

````

## Result

````shell

(Streamr_auto_harvest_earning) chimera@chimera-beta:/opt/chimera/streamr/Streamr_auto_harvest_earning$ python main.py --config_path config.yml
2023-12-09 16:49:15,409 - INFO - Connected to vault
2023-12-09 16:49:15,910 - INFO - Enough Balance 10.56549706880025 to claim
2023-12-09 16:49:16,406 - INFO - gas limit is set to 8.79399e-13, with current_gas_price to 7.1286593041e-08 which will result into 8.5543911649e-08 gas price
2023-12-09 16:49:37,258 - INFO - Transaction Hash: 0x7309e1327dd0d1fc438334f1f2163a60cf246b3b5ca50b2283ea61bedacc5b07, Gas Used: 5.57643e-13
````

### Common Error
````shell

2023-12-09 16:48:26,705 - CRITICAL - Authentication failed. Status code: 500 and status {'errors': ['missing password']}

````

## Crontab & shell launcher

use `crontab -e` and add this to run every 5 days. otherwise use crontab generator to feat you goal
gas cost is actually around 0.06$ when I'm writting this, take this in cosideration

````shell
0 0 */5 * * /opt/Streamr_auto_harvest_earning/run_harvest.sh >> /var/log/Streamr_auto_harvest_earning/harvesting.log

````