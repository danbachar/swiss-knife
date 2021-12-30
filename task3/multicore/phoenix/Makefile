# This Makefile requires GNU make.

.PHONY: default all clean

APPS := \
        histogram \
        linear_regression \
        kmeans \
        matrix_multiply \
        pca \
        string_match \
        word_count \
        reverse_index \
#
default: all

all: 
	@$(foreach APP, $(APPS), \
            $(MAKE) -C $(APP) --no-print-directory;)

clean:
	@$(foreach APP, $(APPS), \
            $(MAKE) -C $(APP) clean --no-print-directory;)

