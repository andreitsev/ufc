import os
import sys
from dotenv import load_dotenv
import typing as t

if 'PYTHONPATH' in os.environ:
	PROJECT_PATH = os.environ["PYTHONPATH"]
	sys.path.insert(0, PROJECT_PATH)
else:
	PROJECT_PATH = '..'

import docker
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

from src.common_utils import get_container_ipaddr  


def get_pg_engine(
    postgress_user: t.Optional[str]=None,
    postgress_password: t.Optional[str]=None,
    postgress_ipaddr: t.Optional[str]=None,
) -> Engine:
    """Returns initialized engine to use is in pd.sql('...', engine)"""
    
    if postgress_ipaddr is None:
        docker_client = docker.from_env()
        pg_container = [container for container in docker_client.containers.list() 
        if 'pgdatabase' in str(container.name).lower()]
        assert len(pg_container) == 1, 'There should be only one postgres container!'
        pg_container = pg_container[0]
        postgress_ipaddr = get_container_ipaddr(pg_container)

    if (
          postgress_user is None or 
          postgress_password is None or 
          postgress_ipaddr is None 
        ):
          load_dotenv()


    postgress_user = (
	    postgress_user if postgress_user is not None
	    else os.getenv("POSTGRES_USER", "")
    )
    postgress_password = (
	    postgress_password if postgress_password is not None
	    else os.getenv("POSTGRES_PASSWORD", "")
    )
    postgress_ipaddr = (
	    postgress_ipaddr if postgress_ipaddr is not None
	    else os.getenv("POSTGRES_IPADDR", "")
    )
    
    eng = create_engine(
        f'postgresql+psycopg2://{postgress_user}:{postgress_password}@{postgress_ipaddr}'
    )
    eng.connect()
    return eng
