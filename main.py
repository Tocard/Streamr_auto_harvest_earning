import click
import logging

from config import load_config
from harvest_sponsorship import collect_earning


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@click.command()
@click.option('--config_path', required=True, help='config path to config.yml')
def main(config_path):
    cfg = load_config(config_path)
    collect_earning(cfg)


if __name__ == '__main__':
    main()
