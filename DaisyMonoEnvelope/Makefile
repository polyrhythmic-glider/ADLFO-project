# Nome del firmware e sorgenti C++.
TARGET = DaisyMonoEnvelope
CPP_SOURCES = main.cpp EnvelopeGenerator.cpp

# Il progetto si trova in ADLFO-Project/DaisyMonoEnvelope e le librerie locali
# sono in Documenti/DaisyExamples. Entrambi i percorsi restano sovrascrivibili:
# make LIBDAISY_DIR=/percorso/libDaisy DAISYSP_DIR=/percorso/DaisySP
LIBDAISY_DIR ?= ../../DaisyExamples/libDaisy
DAISYSP_DIR ?= ../../DaisyExamples/DaisySP

# Questa prima prova viene caricata direttamente nella flash interna STM32.
APP_TYPE ?= BOOT_NONE

ifeq ($(wildcard $(LIBDAISY_DIR)/core/Makefile),)
$(error libDaisy non trovata in "$(LIBDAISY_DIR)". Vedere README.md)
endif

ifeq ($(wildcard $(DAISYSP_DIR)/Makefile),)
$(error DaisySP non trovata in "$(DAISYSP_DIR)". Vedere README.md)
endif

SYSTEM_FILES_DIR = $(LIBDAISY_DIR)/core
include $(SYSTEM_FILES_DIR)/Makefile
