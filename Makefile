.POSIX:
LANG = c
SRC = tree-sitter-$(LANG).c parser.c
OBJ = $(SRC:.c=.o)
CFLAGS = -O0 -g3 -Wall

ifeq ($(OS),Windows_NT)
	SOEXT ?= dll
endif
ifeq ($(shell uname),Darwin)
	SOEXT ?= dylib
else
	SOEXT ?= so
endif

tree-sitter-$(LANG).$(SOEXT): grammar.js.dump $(OBJ)
	$(CC) -shared $(CFLAGS) $(OBJ) -o $@

tree-sitter-$(LANG).o: tree-sitter-lang.c.in
	sed 's/LANG/$(LANG)/g' $< > tree-sitter-$(LANG).c
	$(CC) $(CFLAGS) -c tree-sitter-$(LANG).c -o $@

grammar.js.dump: grammar.js
	xxd -i < grammar.js > grammar.js.dump

clean:
	rm -f *.$(SOEXT) $(OBJ) grammar.js.dump tree-sitter-$(LANG).c

.PHONY: clean
