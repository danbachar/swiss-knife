import sys
import subprocess
import time

FOLDERS = ['.phoronix-test-suite', 'phoronix-test-suite']
def execute_env(FS):

    print("################################################################")
    print("fetching home")
    print("################################################################")
    home_cmd = 'echo $HOME'
    home_proc = subprocess.Popen(home_cmd, shell=True, stdout=subprocess.PIPE)
    global home
    home = home_proc.stdout.readline().decode("utf-8").rstrip()
    print("home is: "+ home)
   
    for system in FS:
        print("################################################################")
        print("benchmark: "+ system)
        print("################################################################")
        print("################################################################")
        print("copying files in "+ system)
        print("################################################################")
        cp_config = 'sudo cp -r .phoronix-test-suite ' + system
        copy1 = subprocess.Popen(cp_config,shell=True, stdout=subprocess.PIPE)
        copy1.wait()
        cp_bench = 'sudo cp -r phoronix-test-suite ' + system
        copy2 = subprocess.Popen(cp_bench,shell=True, stdout=subprocess.PIPE)
        copy2.wait()
        print("################################################################")
        print("symlinking "+ system)
        print("################################################################")

        symlink_proc = 'sudo ln -sfn  '+ system + 'phoronix-test-suite ' + home
        subprocess.Popen(symlink_proc, shell=True,stdout=subprocess.PIPE)

        symlink_conf = 'sudo ln -sfn  '+ system + '.phoronix-test-suite ' + home
        subprocess.Popen(symlink_conf, shell=True,stdout=subprocess.PIPE)

        print("################################################################")
        print("benchmarking...")
        print("################################################################")
        bench_proc = 'sudo ' + home + '/phoronix-test-suite/phoronix-test-suite benchmark fs-mark'
        bench_fs = subprocess.Popen(bench_proc, shell=True)
        bench_fs.wait() 
    print("################################################################")
    print("cleaning up...")
    print("################################################################")
    for system in FS:
        clean_proc = 'sudo rm -rf '+ system + 'phoronix-test-suite '
        subprocess.Popen(clean_proc, shell=True,stdout=subprocess.PIPE)
        clean_conf = 'sudo rm -rf '+ system + '.phoronix-test-suite ' 
        subprocess.Popen(clean_conf, shell=True,stdout=subprocess.PIPE)
    clean_home = 'sudo rm '+ home+ '/phoronix-test-suite' 
    subprocess.Popen(clean_home, shell=True,stdout=subprocess.PIPE)
    clean_conf = 'sudo rm '+ home+ '/.phoronix-test-suite' 
    subprocess.Popen(clean_conf, shell=True,stdout=subprocess.PIPE)

