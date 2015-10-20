#!/usr/bin/env python3
import logging
import os

import boto3

CONTENT_TYPES = {
    '.json' : 'appication/json',
    '.html' : 'text/html',
    '.css'  : 'text/css',
    '.js'   : 'application/javascript',
    '.gif'  : 'image/gif',
    '.png'  : 'image/png',
    '.jpeg' : 'image/jpg',
    '.jpg'  : 'image/jpg',
}


LOGGER = logging.getLogger(__name__)

def _get_content_type(source):
    for k, v in CONTENT_TYPES.items():
        if source.endswith(k):
            return v
    LOGGER.warn("Falling back to octet-stream for %s", source)
    return 'application/octet-stream'


def go(config, env):
    s3 = boto3.resource('s3', region_name='us-west-2')
    LOGGER.info("Uploading to S3 bucket %s", config['upload']['bucket'])
    bucket = s3.Bucket(config['upload']['bucket'])
    for _, outputpath in env.output():
        LOGGER.info("Uploading %s", outputpath)
        fullpath = os.path.join(env.output_path, outputpath)
        with open(fullpath, 'rb') as f:
            content = f.read()
            bucket.put_object(
                Key=outputpath,
                Body=content,
                ACL='public-read',
                ContentType=_get_content_type(outputpath),
                )
