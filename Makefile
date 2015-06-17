name = gw2miner
path = $(shell echo $(shell pwd) | sed 's/[\\/&]/\\\\&/g')

all: build install

build:
	apt-get install -y python-pip
	pip install peewee flask PyMySQL
	python -m compileall src/
	mv src/*.pyc bin/
	chmod +x bin/*.pyc
	cp -n defaults.ini settings.ini

install:
	cp src/service.sh /etc/init.d/$(name)
	sed -i "s/service_name/$(name)/g" /etc/init.d/$(name)
	sed -i "s/run_path/$(path)/g" /etc/init.d/$(name)
	chmod +x /etc/init.d/$(name)
	update-rc.d $(name) defaults

defaults:
	@make all
	rm -f settings.ini
	cp defaults.ini settings.ini

verbose:
	@make all
	sed -ie "s/verbose\s\{0,\}=\s\{0,\}False/verbose=True/g" settings.ini

noverbose:
	@make all
	sed -ie "s/verbose\s\{0,\}=\s\{0,\}True/verbose=False/g" settings.ini

clean:
	rm -f *.pid
	rm -f bin/*.pyc
	rm -f /etc/init.d/$(name)
	update-rc.d -f $(name) remove
