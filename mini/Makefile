FIRMWARE = blackbox-3.1.9.bin
THEME    = theme.json
PATCH    = output/patch.json
OUTPUT   = output/BLACKBOX.BIN

.PHONY: all dry clean help

all: $(OUTPUT)

$(PATCH): $(THEME) $(FIRMWARE)
	@mkdir -p output
	python3 theme2patch.py $< --firmware $(FIRMWARE) -o $@

$(OUTPUT): $(PATCH) $(FIRMWARE)
	python3 patch.py $(FIRMWARE) -o $@ --patch-file $(PATCH)

dry: $(PATCH)
	python3 patch.py $(FIRMWARE) --patch-file $(PATCH) --dry-run

clean:
	rm -rf output

help:
	@echo "make           build output/BLACKBOX.BIN from theme.json"
	@echo "make dry       show patch operations without writing"
	@echo "make clean     remove output/"
