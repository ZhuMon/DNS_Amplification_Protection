# Project
## Dependency
* Update pip
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
```
* install python dependencies
``` 
pip install -r requirements.txt
```
* Update scapy by wget
```
$ cd /tmp
$ wget --trust-server-names https://github.com/secdev/scapy/archive/master.zip
$ unzip master
$ cd scapy-master
sudo python setup.py install
```

## Start
```
$ git clone https://github.com/ZhuMon/DNS_Amplification_Protection.git
$ cd DNS_Amplification_Protection/project/source
$ make
```
