name = gw2miner2
path = $(shell echo $(shell pwd) | sed 's/[\\/&]/\\\\&/g')

all: build install

build:
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
	@make build
	@make install
	rm -f settings.ini
	cp defaults.ini settings.ini

verbose:
	@make build
	@make install
	sed -ie "s/verbose\s\{0,\}=\s\{0,\}False/verbose=True/g" settings.ini

noverbose:
	@make build
	@make install
	sed -ie "s/verbose\s\{0,\}=\s\{0,\}True/verbose=False/g" settings.ini

clean:
	rm -f *.pid
	rm -f bin/*.pyc
	rm -f /etc/init.d/$(name)
	update-rc.d -f $(name) remove
