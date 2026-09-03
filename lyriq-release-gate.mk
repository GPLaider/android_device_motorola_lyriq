# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

ifndef LYRIQ_PRODUCTION_GATE_STAMP
$(error LYRIQ_PRODUCTION_GATE_STAMP is required; run verify_source.py --prebuilts first)
endif

ifneq ($(wildcard $(LYRIQ_PRODUCTION_GATE_STAMP)),)
include $(LYRIQ_PRODUCTION_GATE_STAMP)
else
$(error Lyriq production gate stamp does not exist)
endif

ifneq ($(LYRIQ_PRODUCTION_GATE_STATUS),OK)
$(error Lyriq production input gate did not pass)
endif
ifneq ($(LYRIQ_GATE_DEVICE),lyriq)
$(error Lyriq production stamp belongs to another device)
endif
ifneq ($(LYRIQ_GATE_STOCK_PAYLOAD_BUILD),V1TLS35.73-60-3-10/40dcc-72d036)
$(error Lyriq production stamp belongs to another stock payload build)
endif
ifneq ($(LYRIQ_GATE_CONTRACT_SHA256),c98bb0ee434ef6e469a6016210e8851c1480d7d8fad6d48b85bf2031cd42334a)
$(error Lyriq production stamp belongs to another input contract)
endif
