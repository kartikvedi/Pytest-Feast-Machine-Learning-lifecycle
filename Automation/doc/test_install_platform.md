@startuml sdf

title WEB platform installation

[*] --> do_shell_install
state do_shell_install 
state st_http_ready

do_shell_install --> st_http_ready
state WebInstall 

state "Web configuration" as WebInstall {

  state st_login_form_absent
  state st_login_form_present
  state st_progress
  state st_gw_ready
  state st_gw_not_ready
  state st_locked_down
  state st_not_locked
  
  state do_check_login_form <<choice>>
  state do_check_gw_ready <<choice>> 
  state do_check_lockdown <<choice>>
  
  state do_submit1
  state do_auth
  state do_lockdown
  state do_exit_lockdown
  state do_configure_gw
  state do_configure_nodes

  st_http_ready --> do_check_login_form
  st_http_ready --> st_http_ready : Wait
  do_check_login_form --> st_login_form_present
  do_check_login_form --> st_login_form_absent
  st_login_form_absent --> do_submit1
  st_login_form_present --> do_auth
  do_auth -> do_check_gw_ready
  do_submit1 --> st_progress
  st_progress --> st_gw_not_ready
  do_check_gw_ready --> st_gw_ready
  do_check_gw_ready --> st_gw_not_ready
  st_gw_not_ready --> do_check_lockdown
  do_check_lockdown --> st_locked_down
  do_check_lockdown --> st_not_locked
  st_not_locked --> do_lockdown
  do_lockdown --> do_configure_gw
  st_locked_down --> do_configure_gw
  do_configure_gw -> do_exit_lockdown
  st_gw_ready --> do_configure_nodes
  do_exit_lockdown --> st_gw_ready
}

do_configure_nodes --> [*]

@enduml

# Tests on Platform with SSL
For running tests on ssl platform, ssl certificate in Jupyter notebook is required. Upload .cert file in ~/ notebook directory with the name <em>ca.cert</em>. 

# S3 MinIO test
For running s3 test , deploy mlflow-server first. Then edit yaml notebook file before creation with <strong>mlflow-cluster-name</strong> and <strong>mlflow-secret-name</strong>:
```
connections:
  clusters:
   - mlflow-cluster-name
  secrets:
   - mlflow-secret-name
```

Install platform state machine
@startuml
[*] --> OSInstall
OSInstall : Jenkins JOB
OSInstall --> CLIinstall

CLIinstall --> HTTPready
CLIinstall: Binary platform file installation

HTTPready --> InitialPage
HTTPready --> LoginPage
HTTPready: Check web port is accessible

InitialPage --> GatewayLoadBalancer
InitialPage: First entry web page

LoginPage --> GatewayLoadBalancer
LoginPage: Initial step alredy done
LoginPage: Second entry on site

GatewayLoadBalancer -> LockDown
GatewayLoadBalancer: Available only when platform is lockedDown
LockDown -> GatewayLoadBalancer
GatewayLoadBalancer --> ConfigureHosts
ConfigureHosts --> CreateCluster
CreateCluster --> ConfigureAuthentication

ConfigureAuthentication --> CreateTenant
ConfigureAuthentication: LDAP/ActiveDirectory/Local

CreateTenant --> [*]
@enduml

