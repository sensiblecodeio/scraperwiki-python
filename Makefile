run:    build
	@docker run \
	    --rm \
		-ti \
	    scraperwiki-python

build:
	@docker build -t scraperwiki-python .

.PHONY: run build
