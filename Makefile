deps: vendor

vendor: requirements.txt
	@( \
	    rm -rf vendor env; \
	    virtualenv env; \
	    sed -i -e '1s,^.*$$,#!/usr/bin/env python,g' env/bin/pip; \
	    source env/bin/activate; \
	    mkdir -p vendor; \
	    pip install --target="$$PWD/vendor" -r requirements.txt; \
	    deactivate; \
	    rm -rf env; \
	)

test:
	@tox
