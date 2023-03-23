import os
import sys
import random
import json
from datetime import datetime
import typing as t

if 'PYTHONPATH' in os.environ:
	PROJECT_PATH = os.environ["PYTHONPATH"]
	sys.path.insert(0, PROJECT_PATH)
else:
	PROJECT_PATH = '..'

import docker
import minio
from minio import Minio

from src.common_utils import get_container_ipaddr  


def minio_container_ipaddr(minio_container_name: str='minio') -> str:
    """Return minio container ipaddr as a string"""
    docker_client = docker.from_env()
    minio_container = [
         container for container in docker_client.containers.list() 
        if minio_container_name in str(container.name).lower()
    ]
    assert len(minio_container) == 1, 'There should be only one minio container'
    minio_container = minio_container[0]
    ipaddr = get_container_ipaddr(minio_container)
    return ipaddr

def initialize_minio_client(
		ipaddr: t.Optional[str]=None,
		access_key: t.Optional[str]=None,
		secret_key: t.Optional[str]=None,
		port_number: int=9000,
) -> minio.api.Minio:
    """Returns initialized minio client"""
    if ipaddr is None:
        docker_client = docker.from_env()
        minio_container = [
            container for container in docker_client.containers.list() 
            if 'minio' in str(container.name).lower()
        ]
        assert len(minio_container) == 1, 'There should be only one minio container'
        minio_container = minio_container[0]
        ipaddr = get_container_ipaddr(container=minio_container)

    minio_access_key = (
	    access_key if access_key is not None else os.getenv('MINIO_ACCESS_KEY', "")
    )
    minio_secret_key = (
	    secret_key if secret_key is not None else os.getenv('MINIO_SECRET_KEY', "")
    )
    minio_client = Minio(
        endpoint=f"{ipaddr}:{port_number}",
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,
    )
    # checking client creation
    assert isinstance(minio_client.list_buckets(), list), \
	    'minio_client if not initialized!'
    
    return minio_client

def load_json_from_minio(
    minio_client: minio.api.Minio,
    bucket_name: str='ufc-raw-data',
    object_name: str='ufc_stats.json',
) -> object:
    """Minio -> local -> load local -> delete local"""

    try:
        now_str = str(datetime.now().strftime(format='%Y%m%d%H%M%S%m'))
    except: 
        now_str = 'abc124'
    random_number = str(int(random.random()*1e6))

    tmp_data_local_path = now_str + random_number + '.json'
    minio_client.fget_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=tmp_data_local_path,
    )

    loaded_object = json.load(open(tmp_data_local_path, mode='r', encoding='utf-8'))
    os.remove(tmp_data_local_path)
    return loaded_object


def save_json_to_minio(
    obj: t.Any,
    minio_client: minio.api.Minio,
    bucket_name: str='ufc-raw-data',
    object_name: str='ufc_stats.json',
) -> None:
    """save local -> put from local to minio -> delete local"""

    try:
        now_str = str(datetime.now().strftime(format='%Y%m%d%H%M%S%m'))
    except: 
        now_str = 'abc124'
    random_number = str(int(random.random()*1e6))

    tmp_data_local_path = now_str + random_number + '.json'
    json.dump(
         obj, 
         open(tmp_data_local_path, mode='w', encoding='utf-8'), 
         ensure_ascii=False, indent=2
    )

    minio_client.fput_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=tmp_data_local_path,
    )
    os.remove(tmp_data_local_path)
    return 
