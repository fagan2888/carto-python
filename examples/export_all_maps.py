import argparse
import logging
import os
import warnings
import time
from pathlib import Path
import requests
# we are adding the tqdm module to create a progress bar
from tqdm import tqdm

from carto.auth import APIKeyAuthClient
from carto.visualizations import VisualizationManager

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format=' %(asctime)s - %(levelname)s - %(message)s',
    datefmt='%I:%M:%S %p')
logger = logging.getLogger()

# set input arguments
parser = argparse.ArgumentParser(
    description='Exports all maps')

parser.add_argument('--organization', type=str, dest='organization',
                    default=os.environ.get('CARTO_ORG'),
                    help='Set the name of the organization' +
                    ' account (defaults to env variable CARTO_ORG)')

parser.add_argument('--base_url', type=str, dest='CARTO_BASE_URL',
                    default=os.environ.get('CARTO_BASE_URL'),
                    help='Set the base URL. For example:' +
                    ' https://username.carto.com/ ' +
                    '(defaults to env variable CARTO_BASE_URL)')

parser.add_argument('--api_key', dest='CARTO_API_KEY',
                    default=os.environ.get('CARTO_API_KEY'),
                    help='Api key of the CARTO account' +
                    ' (defaults to env variable CARTO_API_KEY)')

args = parser.parse_args()


# Authenticate to CARTO account
if args.CARTO_BASE_URL and args.CARTO_API_KEY and args.organization:
    auth_client = APIKeyAuthClient(
        args.CARTO_BASE_URL, args.CARTO_API_KEY, args.organization)
else:
    logger.error(
        '''You need to provide valid credentials,
            run with -h parameter for details''')
    import sys
    sys.exit(1)

# create output folder if it doesn't exist
if not os.path.exists('output'):
    logger.info('Creating output folder to store results')
    os.makedirs('output')

# initialize VisualizationManager manager
vis_manager = VisualizationManager(auth_client)

logger.info('Retrieving map data from {base_url}'.format(base_url=args.CARTO_BASE_URL))
# Get all maps from account
maps = vis_manager.all()

logger.info('Downloading {maps} maps'.format(maps=len(maps)))

current_path = Path.cwd()
logger.info('Data will be downloaded into {current_path}/output'.format(current_path=current_path))
# iterate over each map
'''
    The tqdm module is not needed and we could iterate directly over the maps array.
    However, we added this module to have a nicer way to see the download progress.
'''
for viz in tqdm(maps):
    # Get map object using map name
    map_obj = vis_manager.get(viz.name)
    try:
        # get URL to export map
        url = map_obj.export()
    except Exception as e:
        logger.error(str(e))
        continue
    logger.debug(url)
    # make request to the export URL
    r = requests.get(url)
    data_path = current_path / 'output' / "{viz_name}.carto".format(viz_name=viz.name)
    # write download data into a file
    data_path.write_bytes(r.content)
