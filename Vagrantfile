# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  config.vm.box = "debian/wheezy64"
  config.vm.network :forwarded_port, host: 8080, guest: 8080
  config.vm.box_check_update = false
  config.vm.provision :shell, path: "vagrant/bootstrap.sh"

  config.vm.provider "virtualbox" do |v|
    v.memory = 4096
    v.cpus = 2
  end
end
