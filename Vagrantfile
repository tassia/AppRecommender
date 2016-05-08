# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  config.vm.box = "debian/jessie64"
  config.vm.box_check_update = false
  config.vm.network :forwarded_port, host: 8080, guest: 8080
  config.vm.provision :shell, path: "vagrant/bootstrap.sh", privileged: false
  config.vm.provider "virtualbox" do |vm|
    vm.memory = 1024
    vm.cpus = 2
  end
end
