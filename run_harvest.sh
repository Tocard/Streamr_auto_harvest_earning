#!/bin/bash

INSTALL=/opt/Streamr_auto_harvest_earning

source ${INSTALL}/bin/activate

python ${INSTALL}/main.py --config_path /etc/Streamr_auto_harvest_earning/config.yml


