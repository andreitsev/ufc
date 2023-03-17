import docker
from docker.models.containers import Container as DockerContainer



def get_container_ipaddr(container: DockerContainer) -> str:
    """Returns the ipaddr of docker container"""
    container_attrs = container.attrs['NetworkSettings']['Networks']
    random_container_key = list(container_attrs.keys())[0]
    ipaddr = container_attrs[random_container_key]['IPAddress']
    return str(ipaddr)
