# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  config.vm.box_check_update = false
  config.vm.provision :shell, path: "vagrant/bootstrap.sh"

  config.vm.define 'jessie' do |jessie|
    jessie.vm.box = "debian/jessie64"
    jessie.vm.network :forwarded_port, host: 8080, guest: 8080
    jessie.vm.provider "virtualbox" do |vm|
      vm.memory = 1024
      vm.cpus = 2
    end
  end

  config.vm.define 'wheezy' do |wheezy|
    wheezy.vm.box = "debian/wheezy64"
    wheezy.vm.network :forwarded_port, host: 8000, guest: 8080
    wheezy.vm.provider "virtualbox" do |vm|
      vm.memory = 1024
      vm.cpus = 2
    end
  end
end
