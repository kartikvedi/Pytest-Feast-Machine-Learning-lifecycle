import os
import sys
import re
import json
import sqlite3
import argparse
from cliobject import CLIObject

ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.append(os.path.join(ROOT_PATH))
from core.platform_prepare import ip_range_to_list, get_latest_build

TPL_PATH = os.path.join(ROOT_PATH, 'configs', 'platform.tpl')
RE_HOST = re.compile(r'(mip\S+vm)(\d+)')
RE_IP_ADDR = re.compile(r'(\d+\.\d+\.\d+\.\d+)')


class HostsDB:
    def __init__(self):
        self._con = None
        self._cur = None
        self.init_db()

    def init_db(self):
        init_db = False
        if not os.path.exists('hosts.db'):
            init_db = True
        self._con = sqlite3.connect('hosts.db')
        self._cur = self._con.cursor()
        if init_db:
            self._cur.execute('''CREATE TABLE hosts (ip text, hostname text)''')

    def print_all_rows(self):
        for row in self._cur.execute("SELECT * FROM hosts"):
            print(row)

    def get_host(self, ip):
        for row in self._con.execute(f'SELECT hostname FROM hosts WHERE ip="{ip}"'):
            return row[0]
        return None

    def add_host(self, ip, hostname):
        self._cur.execute(f'SELECT COUNT(*) FROM hosts WHERE ip="{ip}"')
        if self._cur.fetchone()[0] == 0:
            print(f"Insert new IP: {ip}")
            self._cur.execute(f'INSERT INTO hosts VALUES("{ip}", "{hostname}")')
            self._con.commit()
        else:
            print(f"IP address {ip} already exists")


class EZMLConfig:
    def __init__(self, controller_ip=None, gateway=None, cmasters=None, cworkers=None, dfmasters=None, dfworkers=None,
                 host_passwd=None,
                 config=None, prefix='my', platform_user=None, platform_password=None, ecp_build_id='latest'):
        self._controller_ip = controller_ip
        self._cworkers = cworkers
        self._cmasters = cmasters
        self._dfworkers = dfworkers
        self._dfmasters = dfmasters
        self._gateway = gateway
        self._host_passwd = host_passwd
        self._hosts = []
        self._controller_hosts = []
        self._config = config
        self._prefix = prefix
        self._platform_user = platform_user
        self._platform_password = platform_password
        self._ecp_build_id = ecp_build_id
        self.data = {}


    def get_hostname_by_ip(self, ip):
        _, stdout, _ = CLIObject().exec_cmd_from_args(ip=ip, password=self._host_passwd, cmd='hostname')
        hostname = stdout.read(128)
        hn = hostname.decode('utf8').strip()
        return hn

    def get_ip_by_role(self, role):
        if role in self.data:
            if role in ["controller", "gateway"]:
                return self.data[role]["ip"]
            else:
                return self.data[role]["ips"]


    def get_hostname_by_role(self, role):
        if role in self.data:
            if role in ["controller", "gateway"]:
                return self.data[role]["hostname"]
            else:
                return self.data[role]["hostnames"]


    def apply_config(self, controller_ip, gateway_ip, gateway_hostname, ip_list, host_list, cmaster_nodes,
                     cworker_nodes, dfmaster_nodes, dfworker_nodes, http_type='http', ecp_build_id=None):
        self._config['platform_bin_url'] = self._config['platform_bin_url'].replace('{BUILD_ID}', str(ecp_build_id))
        self._config['controller_ip'] = controller_ip
        self._config['url'] = http_type + '://' + controller_ip
        self._config['gateway_lb_ip'] = gateway_ip
        self._config['gateway_lb_hostname'] = gateway_hostname
        self._config['hosts']['ips_list'] = ','.join(ip_list)
        self._config['hosts']['hosts_list'] = ','.join(host_list)
        for cluster in range(0, len(self._config['clusters'])):
            if "datafabric" in self._config['clusters'][cluster] and \
                    self._config['clusters'][cluster]["datafabric"] == True:
                self._config['clusters'][cluster]['master_nodes'] = dfmaster_nodes['ips']
                self._config['clusters'][cluster]['worker_nodes'] = dfworker_nodes['ips']
                self._config['clusters'][cluster]['master_nodes_hostnames'] = dfmaster_nodes['hostnames']
                self._config['clusters'][cluster]['worker_nodes_hostnames'] = dfworker_nodes['hostnames']
            else:
                self._config['clusters'][cluster]['master_nodes'] = cmaster_nodes['ips']
                self._config['clusters'][cluster]['worker_nodes'] = cworker_nodes['ips']
                self._config['clusters'][cluster]['master_nodes_hostnames'] = cmaster_nodes['hostnames']
                self._config['clusters'][cluster]['worker_nodes_hostnames'] = cworker_nodes['hostnames']
        if self._platform_user:
            self._config['login'] = self._platform_user
            self._config['tenant']['user_name'] = self._platform_user
        if self._platform_password:
            self._config['password'] = self._platform_password
            self._config['admin_password'] = self._platform_password
            self._config['auth']['bind_pwd'] = self._platform_password


    def parse_hosts(self, role, v):
        ips, hostnames = [], []
        if v is not None:
            v = v.strip().split(",")
            for ip in v:
                if RE_IP_ADDR.search(ip):  # full ip present
                    hn = self.get_hostname_by_ip(ip)
                    ips += [ip]
                    hostnames += [hn]
                else:  # ip range string
                    ip_str = '{0}.{1}'.format('.'.join(self._controller_ip.split(".")[0:3]), ip)
                    ip_list = ip_range_to_list(ip_str)
                    for ip in ip_list:
                        hn = self.get_hostname_by_ip(ip)
                        ips += [ip]
                        hostnames += [hn]
            if role == "controller":
                self.data[role] = {"ip": ips[0], "hostname": hostnames[0]}
            elif role == "gateway":
                self.data[role] = {"ip": ips[0], "hostname": hostnames[0]}
            else:
                self.data[role] = {"ips": ips, "hostnames": hostnames}
        else:
            self.data[role] = {"ips": [], "hostnames": []}

    def load_config(self, json_filepath):
        self._config = json.load(open(json_filepath, 'r'))
        self._controller_ip = self._config['controller_ip']
        self._gateway = self._config['gateway_lb_ip']
        # self._masters = self._config['clusters'][0]['master_nodes']
        # self._workers = self._config['clusters'][0]['worker_nodes']
        # self._hosts = self._config['hosts']['host_list']

        self.parse_hosts('controller', self._controller_ip)
        self.parse_hosts('gateway', self._gateway)
        # self.parse_hosts('masters', self._masters)
        # self.parse_hosts('workers', self._workers)

    def save_config(self, output_json):
        data = self.render_config()
        with open(output_json, 'w', encoding='utf-8') as outfile:
            outfile.write(data)

    def render_config(self):
        self.parse_hosts('controller', self._controller_ip)
        self.parse_hosts('gateway', self._gateway)
        self.parse_hosts('cmasters', self._cmasters)
        self.parse_hosts('cworkers', self._cworkers)
        self.parse_hosts('dfmasters', self._dfmasters)
        self.parse_hosts('dfworkers', self._dfworkers)
        if self._ecp_build_id == 'latest':
            self._ecp_build_id = get_latest_build(
                'http://bd-artifactory.mip.storage.hpecorp.net:80/artifactory/hpe-cp-eng-builds/debug/5.4/centos7')

        ips_list = []
        hosts_list= []

        for role in ['controller', 'gateway', 'cmasters','cworkers', 'dfmasters','dfworkers']:
            if role in ['controller', 'gateway']:
                ips_list.append(self.get_ip_by_role(role))
                hosts_list.append(self.get_hostname_by_role(role))
            else:
                ips_list.extend(self.get_ip_by_role(role))
                hosts_list.extend(self.get_hostname_by_role(role))


        self.apply_config(
            controller_ip=self.get_ip_by_role('controller'),
            gateway_ip=self.get_ip_by_role('gateway'),
            gateway_hostname=self.get_hostname_by_role('gateway'),
            ip_list=ips_list,
            host_list=hosts_list,
            cmaster_nodes=self.data['cmasters'],
            cworker_nodes=self.data['cworkers'],
            dfmaster_nodes=self.data['dfmasters'],
            dfworker_nodes=self.data['dfworkers'],
            http_type='http',
            ecp_build_id=self._ecp_build_id
        )

        data = json.dumps(self._config, ensure_ascii=False, indent=2)
        data = data.replace('{USER}', self._prefix)
        return data


if __name__ == '__main__':
    '''
        Generate platform config for testing
        Example:
            ./bin/mkconfig --controller=16.0.12.234 --gateway=232\
                --workers=238-240 --masters=235
    '''
    parser = argparse.ArgumentParser(description='EZML config generator.')
    parser.add_argument('--controller_ip', required=False, type=str, help='Full IP of controller host')
    parser.add_argument('--gateway', required=False, type=str, help='Gateway IP or last octet value')
    parser.add_argument('--cworkers', required=False, type=str, help='Workers nodes IP range')
    parser.add_argument('--cmasters', required=False, type=str, help='Masters nodes IP range')
    parser.add_argument('--dfworkers', required=False, type=str, help='Workers nodes IP range', default="")
    parser.add_argument('--dfmasters', required=False, type=str, help='Masters nodes IP range')
    parser.add_argument('--output', type=str, help='Output test config json file name path')
    parser.add_argument('--prefix', type=str, help='Masters nodes IP range')
    parser.add_argument('--platform_user', type=str, help='', default='dev1')
    parser.add_argument('--platform_password', type=str, help='', default='admin123')
    parser.add_argument('--ecp_build_id', type=str,
                        help='Build number of ECP platform from server bd-artifactory.mip.storage.hpecorp.net',
                        default='latest')
    parser.add_argument('--input_json', required=False, type=str, help='Input platform config in json format')

    args = parser.parse_args()

    #
    # Load platform config
    #
    platform_config = {}
    if args.input_json:
        platform_config = json.load(open(args.input_json, 'r'))

    #
    # Override config with command line arguments
    #
    for v in [x for x in dir(args) if not x.startswith('_')]:
        o = getattr(args, v)
        if o:
            platform_config[v] = o

    default_conf = json.load(open(TPL_PATH, 'r'))
    '''
    ezcfg = EZMLConfig(platform_config['controller_ip'], gateway=platform_config['gateway'],
                       cworkers=platform_config['cworkers'],
                       cmasters=platform_config['cmasters'],
                       dfworkers=platform_config['dfworkers'],
                       dfmasters=platform_config['dfmasters'],
                       host_passwd=os.environ['host_passwd'],
                       config=default_conf,
                       prefix=platform_config['prefix'],
                       platform_user=platform_config['platform_user'],
                       platform_password=platform_config['platform_password'],
                       ecp_build_id=platform_config['ecp_build_id'])
    '''

    # ezcfg = EZMLConfig()
    # ezcfg.load_config(os.path.join(ROOT_PATH, args.json))

    # ezcfg = EZMLConfigSQLite(args.controller, gateway=args.gateway, workers=args.workers, masters=args.masters,
    #                          host_passwd=os.environ['host_passwd'], template=args.template, output='config.db')

    ezcfg = EZMLConfig(controller_ip="10.1.100.146",
                       gateway="10.1.100.147",
                       cworkers="10.1.100.152",
                       cmasters="10.1.100.153",
                       dfworkers=None,
                       dfmasters="10.1.100.148,10.1.100.149,10.1.100.150",
                       host_passwd="admin123",
                       config=default_conf,
                       prefix="bvt",
                       platform_user="root",
                       platform_password="admin123",
                       ecp_build_id="123")
    print(ezcfg.render_config())
    json_output = args.output
    #if not args.output:
    #   json_output = os.path.join(ROOT_PATH, 'platform.json')
    ezcfg.save_config(json_output)
