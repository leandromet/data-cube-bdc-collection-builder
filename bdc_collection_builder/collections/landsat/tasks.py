# Python Native
import logging
import os
from datetime import datetime

# 3rdparty
from glob import glob as resource_glob
from psycopg2 import InternalError
from requests import get as resource_get
from sqlalchemy.exc import InvalidRequestError

# Builder
from bdc_collection_builder.celery import celery_app
from bdc_collection_builder.config import Config
from bdc_collection_builder.core.utils import upload_file
from bdc_collection_builder.collections.base_task import RadcorTask
from bdc_collection_builder.collections.landsat.download import download_landsat_images
from bdc_collection_builder.collections.landsat.publish import publish
from bdc_collection_builder.collections.utils import get_task_activity


class LandsatTask(RadcorTask):
    def get_tile_id(self, scene_id, **kwargs):
        fragments = scene_id.split('_')
        return fragments[2]

    def get_tile_date(self, scene_id, **kwargs):
        fragments = scene_id.split('_')

        return datetime.strptime(fragments[3], '%Y%m%d')

    def download(self, scene):
        # Create/Update activity
        activity_history = self.create_execution(scene)

        try:
            scene_id = scene['sceneid']
            yyyymm = self.get_tile_date(scene_id).strftime('%Y-%m')
            activity_args = scene.get('args', {})

            collection_item = self.get_collection_item(activity_history.activity)

            # Output product dir
            productdir = os.path.join(activity_args.get('file'), '{}/{}'.format(yyyymm, self.get_tile_id(scene_id)))

            if not os.path.exists(productdir):
                os.makedirs(productdir)

            file = download_landsat_images(activity_args['link'], productdir)

            collection_item.compressed_file = file.replace(Config.DATA_DIR, '')

            cloud = activity_args.get('cloud')

            if cloud:
                collection_item.cloud_cover = cloud

            activity_args['file'] = file
        except BaseException as e:
            logging.error('An error occurred during task execution', e)

            raise e

        collection_item.save()

        scene['args'] = activity_args

        # Create new activity 'correctionS2' to continue task chain
        scene['activity_type'] = 'correctionLC8'

        return scene

    def publish(self, scene):
        scene['activity_type'] = 'publishLC8'

        # Create/Update activity
        activity_history = self.create_execution(scene)

        try:
            assets = publish(self.get_collection_item(activity_history.activity), activity_history.activity)
        except BaseException as e:
            logging.error('An error occurred during task execution', e)

            raise e

        scene['activity_type'] = 'uploadLC8'
        scene['args']['assets'] = assets

        return scene

    def upload(self, scene):
        scene['activity_type'] = 'uploadLC8'

        # Create/Update activity
        self.create_execution(scene)

        assets = scene['args']['assets']

        for entry in assets.values():
            file_without_prefix = entry['asset'].replace('{}/'.format(Config.AWS_BUCKET_NAME), '')
            upload_file(entry['file'], Config.AWS_BUCKET_NAME, file_without_prefix)

    @staticmethod
    def espa_done(productdir, pathrow, date):
        template = os.path.join(productdir, 'LC08_*_{}_{}_*.tif'.format(pathrow, date))

        fs = resource_glob(template)

        return len(fs) > 0

    def correction(self, scene):
        # Set Collection to the Sentinel Surface Reflectance
        scene['collection_id'] = 'LC8SR'
        scene['activity_type'] = 'correctionLC8'
        scene_id = scene['sceneid']

        # Create/Update activity
        execution = self.create_execution(scene)

        try:
            params = dict(
                app=scene['activity_type'],
                sceneid=scene['sceneid'],
                file=scene['args']['file']
            )

            pathrow = self.get_tile_id(scene_id)
            tile_date = self.get_tile_date(scene_id)
            yyyymm = tile_date.strftime('%Y-%m')
            date = tile_date.strftime('%Y%m%d')

            params['pathrow'] = pathrow

            # Send scene to the ESPA service
            req = resource_get('{}/espa'.format(Config.ESPA_URL), params=params)
            # Ensure the request has been successfully
            assert req.status_code == 200

            result = req.json()

            if result and result.get('status') == 'ERROR':
                raise RuntimeError('Error in espa-science execution - {}'.format(scene_id))

            # Product dir
            productdir = os.path.join(Config.DATA_DIR, 'Repository/Archive/{}/{}/{}'.format(scene['collection_id'], yyyymm, pathrow))

            logging.info('Checking for the ESPA generated files in {}'.format(productdir))

            if not LandsatTask.espa_done(productdir, pathrow, date):
                raise RuntimeError('Error in atmospheric correction')

            scene['args']['file'] = productdir

        except BaseException as e:
            logging.error('Error at correction Landsat {}, id={} - {}'.format(scene_id, execution.activity_id, str(e)))

            raise e

        scene['activity_type'] = 'publishLC8'

        return scene


@celery_app.task(base=LandsatTask, queue='download')
def download_landsat(scene):
    return download_landsat.download(scene)


@celery_app.task(base=LandsatTask, queue='atm-correction')
def atm_correction_landsat(scene):
    return atm_correction_landsat.correction(scene)


@celery_app.task(base=LandsatTask, queue='publish', max_retries=3, autoretry_for=(InternalError, InvalidRequestError,), default_retry_delay=Config.TASK_RETRY_DELAY)
def publish_landsat(scene):
    return publish_landsat.publish(scene)


@celery_app.task(base=LandsatTask, queue='upload')
def upload_landsat(scene):
    upload_landsat.upload(scene)