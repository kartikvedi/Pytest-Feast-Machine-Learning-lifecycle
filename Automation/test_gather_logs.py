import re
import logging
import pytest

_log = logging.getLogger(__name__)


def test_gather_master_host(config, exec_cmd_with_output_handler):
    if 'logs' in config:
        logs = config['logs']
        for log in logs:
            _log.info('Gather log file: ' + log['file'])
            with open(log['file'], 'w') as fh:
                _, pods_output = exec_cmd_with_output_handler(log['cmd'])
                fh.write(pods_output)
    else:
        _log.warning('No log section in config file. Collecting logs is disabled.')

def test_gather_notebook_info(config, exec_cmd_with_output_handler):
    notebook = config['notebook']['name']

    tenant = config.get("tenant", None)
    if tenant:
        ns = tenant["namespace"] if 'namespace' in tenant else tenant["name"] 
    else:
        ns = 'dev1'
    #
    # Pass notebook hash version to Jenkins pipeline
    #
    with open('pipeline.dat', 'w') as datfile:
        pod_cmd = 'kubectl get pod -l kubedirector.hpe.com/kdapp=jupyter-notebook -l kubedirector.hpe.com/kdcluster=' + notebook + ' -n ' + ns + ' -o jsonpath="{.items[0].status.containerStatuses[0].imageID}"'
        _, nb_hash = exec_cmd_with_output_handler(pod_cmd)
        nb_hash = nb_hash.strip()
        m = re.search('@sha256:([0-9a-fA-F]{8})', nb_hash)
        if m:
            _log.info(f'Notebook hash: {m.group(1)}')
            datfile.write(f'nb: {m.group(1)}')
        else:
            _log.warning('Unable to fetch notebook hash!')
