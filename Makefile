# Python settings
ifndef TRAVIS
	PYTHON_MAJOR := 2
	PYTHON_MINOR := 7
	ENV := env
else
	# Use the virtualenv provided by Travis
	ENV = $(VIRTUAL_ENV)
endif

# Project settings
PROJECT := Flask-RESTful
PACKAGE := flask_restful
SOURCES := Makefile setup.py $(shell find $(PACKAGE) -name '*.py')
EGG_INFO := $(subst -,_,$(PROJECT)).egg-info

# System paths
PLATFORM := $(shell python -c 'import sys; print(sys.platform)')
ifneq ($(findstring win32, $(PLATFORM)), )
	SYS_PYTHON_DIR := C:\\Python$(PYTHON_MAJOR)$(PYTHON_MINOR)
	SYS_PYTHON := $(SYS_PYTHON_DIR)\\python.exe
	SYS_VIRTUALENV := $(SYS_PYTHON_DIR)\\Scripts\\virtualenv.exe
	# https://bugs.launchpad.net/virtualenv/+bug/449537
	export TCL_LIBRARY=$(SYS_PYTHON_DIR)\\tcl\\tcl8.5
else
	SYS_PYTHON := python$(PYTHON_MAJOR)
	ifdef PYTHON_MINOR
		SYS_PYTHON := $(SYS_PYTHON).$(PYTHON_MINOR)
	endif
	SYS_VIRTUALENV := virtualenv
endif

# virtualenv paths
ifneq ($(findstring win32, $(PLATFORM)), )
	BIN := $(ENV)/Scripts
	OPEN := cmd /c start
else
	BIN := $(ENV)/bin
	ifneq ($(findstring cygwin, $(PLATFORM)), )
		OPEN := cygstart
	else
		OPEN := open
	endif
endif

# virtualenv executables
PYTHON := $(BIN)/python
PIP := $(BIN)/pip
PEP8 := $(BIN)/pep8
FLAKE8 := $(BIN)/flake8
PEP8RADIUS := $(BIN)/pep8radius
PEP257 := $(BIN)/pep257
NOSE := $(BIN)/nosetests
COVERAGE := $(BIN)/coverage

# Remove if you don't want pip to cache downloads
PIP_CACHE_DIR := .cache
PIP_CACHE := --download-cache $(PIP_CACHE_DIR)

# Flags for PHONY targets
DEPENDS_TEST := $(ENV)/.depends-test
DEPENDS_DEV := $(ENV)/.depends-dev
DEPENDS_DOC := $(ENV)/.depends-doc
ALL := $(ENV)/.all

# Main Targets ###############################################################

.PHONY: all
all: depends doc $(ALL)
$(ALL): $(SOURCES)
	$(MAKE) check
	touch $(ALL)  # flag to indicate all setup steps were successful

# Targets to run on Travis
.PHONY: ci
ci: test

# Development Installation ###################################################

.PHONY: env
env: $(PIP)

$(PIP):
	$(SYS_VIRTUALENV) --python $(SYS_PYTHON) $(ENV)
	$(PIP) install wheel

.PHONY: depends
depends: .depends-test .depends-dev .depends-doc

.PHONY: .depends-test
.depends-test: env Makefile $(DEPENDS_TEST)
$(DEPENDS_TEST): Makefile tests/requirements.txt
	$(PIP) install -e .[paging]
	$(PIP) install -r tests/requirements.txt
	touch $(DEPENDS_TEST)  # flag to indicate dependencies are installed

.PHONY: .depends-dev
.depends-dev: env Makefile $(DEPENDS_DEV)
$(DEPENDS_DEV): Makefile
	$(PIP) install $(PIP_CACHE) flake8 pep257 pep8radius
	touch $(DEPENDS_DEV)  # flag to indicate dependencies are installed

.PHONY: .depends-doc
.depends-doc: env Makefile setup.py
$(DEPENDS_DOC): Makefile setup.py
	$(PIP) install -e .[docs]
	touch $(DEPENDS_DOC)  # flag to indicate dependencies are installed

# Documentation ##############################################################

.PHONY: doc
doc: .depends-doc
	cd docs; $(MAKE) html

.PHONY: read
read: doc
	$(OPEN) docs/_build/html/index.html

# Static Analysis ############################################################

.PHONY: check
check: flake8 pep257

PEP8_IGNORED := E501

.PHONY: pep8
pep8: .depends-dev
	$(PEP8) $(PACKAGE) tests --ignore=$(PEP8_IGNORED)

.PHONY: flake8
flake8: .depends-dev
	$(FLAKE8) $(PACKAGE) tests --ignore=$(PEP8_IGNORED)

.PHONY: pep257
pep257: .depends-dev
	$(PEP257) $(PACKAGE)

.PHONY: fix
fix: .depends-dev
	$(PEP8RADIUS) --docformatter --in-place

# Testing ####################################################################

.PHONY: test
test: .depends-test
	$(NOSE) tests --with-coverage --cover-package=$(PACKAGE)

.PHONY: htmlcov
htmlcov: test
	$(COVERAGE) html
	$(OPEN) htmlcov/index.html

# Cleanup ####################################################################

.PHONY: clean
clean: .clean-dist .clean-test .clean-doc .clean-build
	rm -rf $(ALL)

.PHONY: clean-env
clean-env: clean
	rm -rf $(ENV)

.PHONY: clean-all
clean-all: clean clean-env .clean-cache

.PHONY: .clean-build
.clean-build:
	find $(PACKAGE) -name '*.pyc' -delete
	find $(PACKAGE) -name '__pycache__' -delete
	rm -rf $(EGG_INFO)

.PHONY: .clean-doc
.clean-doc:
	rm -rf docs/_build

.PHONY: .clean-test
.clean-test:
	rm -rf .coverage

.PHONY: .clean-dist
.clean-dist:
	rm -rf dist build

.PHONY: .clean-cache
.clean-cache:
	rm -rf $(PIP_CACHE_DIR)

# Release ####################################################################

.PHONY: authors
authors:
    echo "Authors\n=======\n\nA huge thanks to all of our contributors:\n\n" > AUTHORS.md
    git log --raw | grep "^Author: " | cut -d ' ' -f2- | cut -d '<' -f1 | sed 's/^/- /' | sort | uniq >> AUTHORS.md

.PHONY: register
register: doc
	$(PYTHON) setup.py register

.PHONY: dist
dist: doc test
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel

.PHONY: upload
upload: .git-no-changes doc register
	$(PYTHON) setup.py sdist upload
	$(PYTHON) setup.py bdist_wheel upload

.PHONY: .git-no-changes
.git-no-changes:
	@if git diff --name-only --exit-code;         \
	then                                          \
		echo Git working copy is clean...;        \
	else                                          \
		echo ERROR: Git working copy is dirty!;   \
		echo Commit your changes and try again.;  \
		exit -1;                                  \
	fi;

# System Installation ########################################################

.PHONY: develop
develop:
	$(SYS_PYTHON) setup.py develop

.PHONY: install
install:
	$(SYS_PYTHON) setup.py install

.PHONY: download
download:
	pip install $(PROJECT)
