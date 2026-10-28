.PHONY: pcb check test prototype-test
PYTHON ?= .venv/bin/python
CXX ?= c++
pcb:
	$(PYTHON) hardware/pcb/build.py
check:
	$(PYTHON) hardware/pcb/validate.py
test:
	$(CXX) -std=c++14 -Wall -Wextra -Werror platform/tests/ports_test.cpp -o /tmp/adolfo-ports-test
	/tmp/adolfo-ports-test
	$(CXX) -std=c++14 -Wall -Wextra -Werror platform/tests/converter_test.cpp -o /tmp/adolfo-converter-test
	/tmp/adolfo-converter-test
prototype-test:
	$(MAKE) -C Adolfo test
