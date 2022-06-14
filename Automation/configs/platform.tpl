{
  "url": "",
  "controller_ip": "",
  "gateway_lb_ip": "",
  "gateway_lb_hostname": "",
  "login": "dev1",
  "password": "_passwd_",
  "admin_login": "admin",
  "admin_password": "_admin_passwd_",
  "login_timeout_sec": 15,
  "cluster_creation_max_timeout_seconds": 3600,
  "platform_bin_url": "http://bd-artifactory.mip.storage.hpecorp.net/ui/api/v1/download?repoKey=hpe-cp-eng-builds&path=debug%252F5.4%252Fcentos7%252F{BUILD_ID}%252Fhpe-cp-rhel-debug-5.4-{BUILD_ID}.bin",
  "logs": [
    {"cmd": "kubectl get pods -A", "file": "get_pods.log"},
    {"cmd": "kubectl get svc -A", "file": "get_svc.log"}
  ],
  "runtime_configuration": {
    "float_info": {
        "endip": "172.18.255.254",
        "ispingreqd": true,
        "startip": "172.18.0.2",
        "nexthop": "172.18.0.1",
        "mask": 16,
        "extif": "ens192",
        "label": {
            "name": "Default",
            "description": "Floating network range set up during install"
        }
    },
    "containerdisks": [
        "/dev/sdb"
    ],
    "posix_client_type": "basic",
    "tenant_network_isolation": true,
    "kerberos": false,
    "intgatewayip": "172.18.0.1",
    "fqdn_assignment_mode": "index_sequential",
    "routable_network": false,
    "bdshared_global_bddomain": "hpecplocal",
    "bdshared_global_bdprefix": "hpecp-",
    "custom_install_name": "BVT-Testing"
},
  "auth": {
    "auth_type": "Active Directory",
    "security": "LDAPS",
    "service_host": "10.1.100.27",
    "service_port": "636",
    "user_attribute": "sAMAccountName",
    "base_dn": "CN=Users,DC=samdom,DC=example,DC=com",
    "bind_dn": "cn=Administrator,CN=Users,DC=samdom,DC=example,DC=com",
    "bind_pwd": "5ambaPwd@"
  },
  "hosts": {
    "ip_list": "",
    "host_list": [],
    "user": "root",
    "password": "__HOST_PASSWD__",
    "hosts_creation_max_timeout_seconds": 600
  },
  "clusters": [
    {
      "name": "{USER}-compute-cluster",
      "kubernetes_version": "1.20.11",
      "configure_auth": true,
      "apps": {
        "istio": true,
        "kubeflow": true
      },
      "master_nodes": [],
      "worker_nodes": [],
      "datafabric": false
    },
    {
      "name": "{USER}-df-cluster",
      "kubernetes_version": "1.20.11",
      "configure_auth": true,
      "master_nodes": [],
      "worker_nodes": [],
      "datafabric": true
    }
  ],
  "tenant": {
    "name": "{USER}tenant",
    "ext_auth": "cn=Eng,ou=Group,dc=mip,dc=storage,dc=hpecorp,dc=net",
    "ext_auth_role": "Admin",
    "user_name": "dev1",
    "user_role": "Admin",
    "add_secrets": true,
    "namespace": "{USER}tenant"
  },
  "notebook": {
    "name": "{USER}-notebook",
    "command_execution_max_timeout": 600,
    "creation_max_timeout_seconds": 7200,
    "ram": 8,
    "pvc": 128,
    "yaml_data": [
      {
        "section": "clusters:",
        "values": [
          "- trainingengine",
          "- {USER}mlflow"
        ]
      },
      {
        "section": "secrets:",
        "values": [
          "- mlflow-sc",
          "- s3-cred"
        ]
      }
    ]
  },
  "training": {
    "name": "trainingengine",
    "command_execution_max_timeout": 300,
    "creation_max_timeout_seconds": 4200
  },
  "mlflow": {
    "name": "{USER}mlflow",
    "minio_bucket_name": "mlflow",
    "command_execution_max_timeout": 300,
    "creation_max_timeout_seconds": 3600
  },
  "jenkins": {
    "url": "https://ez-jenkins.mip.storage.hpecorp.net:8443",
    "_user": "jenkins",
    "_password": "_jenkins_token_"
  }
}

