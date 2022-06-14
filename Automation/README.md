# Installation
* Download WebDriver (choose by your browser version) https://chromedriver.chromium.org/downloads
* Copy chromedriver into the directory with executable binaries:
    ```
    mkdir $HOME/bin
    export PATH=$PATH:$HOME/bin
    cp chromedriver $HOME/bin
    ```
* Prepare python virtual env:
    ```
    python3 -m venv venv
    . ./venv/bin/activate
    pip install -r requirements.txt
    ```
# Environment configuration
Add to you .bashrc next variables:
* host_passwd       - root password for you VM
* ECP_JENKINS_USER  - your account on https://ez-jenkins.mip.storage.hpecorp.net:8443/
* ECP_JENKINS_TOKEN - api token of you profile on https://ez-jenkins.mip.storage.hpecorp.net:8443/


# Usage tests

* Modify platform.json with your credentials and values.
* Start test
    ```
    pytest -x -v test_notebook.py
    ```
    See *pytest* documentation for command line argumets

If you need to run test with installing (and uninstalling after) external components (ISTIO, DEX, SELDON), use the Makefile scripts.
For choosing an Istio specific version set environment variable ISTIO_VERSION=x.yy.z. By default ISTIO_VERSION=1.12.2
* Start test
    ```
    ISTIO_VERSION=1.11.0 make ext-istio/ext-dex/ext-seldon/ext-all install-externals
    pytest -x -v test_notebook.py
    ISTIO_VERSION=1.11.0 make ext-istio/ext-dex/ext-seldon/ext-all uninstall-externals
    ```
    See other Makefile targets for run complex tests splitted by their appointments.
    There is more useful to specify required test combinations as additional target and wrap it into install-externals/unistall-externals:
    ```
    Makefile:
	mytests:  install-externals .mytests uninstall-externals
	.mytests:
		pytest -x -v test1.py test2.py ...
    ```
    And then run:
    ```
    ISTIO_VERSION=x.yy.z make ext-istio ext-seldon mytests
    ```

# Test configuration

For executing test you need to prepare full test with environment parameters.
You can use generator to create your own configuration. Generator requires few parameters, like IP address of platform and prefix name that would be add to application names, cluster names, etc...
As input data generator used json configuration file and command line arguments.
for more information of supported arguments run:
```
$./bin/mkconfig -h
```
 
Generator execution example:
```
./bin/mkconfig --controller_ip=15.0.12.234 --gateway=233 --masters=235 --workers=238-240
```
You need set full IP only for controller_ip variable. Other arguments can be used in short format. 
Supported formats:
* Full listing: 1.2.3.4, 1.2.3.4.5
* Full address with last octet in range: 1.2.3.4-5
* Short format of last octet range: 4,5,7-9 

On executing test script will determine full list of IP hosts and walks thought to gather hostname of each host. All data will be stored in sqlite database in current directory in file hosts.db. Next time script will use hostname data from database.

# Links
* https://docs.pytest.org/
* https://chromedriver.chromium.org/
* https://selenium-python.readthedocs.io/
