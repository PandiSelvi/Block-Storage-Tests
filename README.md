# Block-Storage-Tests

Testscripts for JCS BS


Scripts and resusable function modules for block storage functional testing Framework:-Unittest

About the scripts:- 

1.test_01.py: Contains the first half Launch Critical testcases

2.test_02.py Other half of functional tests

3.config.py: Input Module with input parameters

4.volume_utils.py: Module with reusable volume functions

5.instance_utils.py: Module with reusable instance functions

6.network_utils.py: Module with reusable network functions

7.image_utils.py: Module with reusable glance functions

8.data_volume: Resuable functions for data operations on volume

9.backup_utils: Module with reusable backup functions

10.common_utils: Module with reusable functions

Initial settings:-

1.Set the Neutron gateway for router

2.Add security group rules to enable ping and ssh

3.Add nova key pair and set permissions(chmod 600 file – owner can read and write)

4.Edit the config file and provide all inputs

Usage:-

1.All the modules should be placed in the python directory

2.python test_01.py

3.Script has setup function if some existing resources found script will exit with error message

4.Has teardown functions which cleans up the whole setup

5.Recommended to run on a fresh setup.
