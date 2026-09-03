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
ifneq ($(LYRIQ_GATE_CONTRACT_ID),$(LYRIQ_STOCK_CONTRACT))
$(error Lyriq production stamp belongs to another stock contract)
endif
ifneq ($(LYRIQ_GATE_STOCK_PAYLOAD_BUILD),$(LYRIQ_STOCK_PAYLOAD_BUILD))
$(error Lyriq production stamp belongs to another stock payload build)
endif
ifneq ($(LYRIQ_GATE_CONTRACT_SHA256),$(LYRIQ_STOCK_CONTRACT_SHA256))
$(error Lyriq production stamp belongs to another input contract)
endif
ifneq ($(LYRIQ_GATE_STOCK_IMS_CONTRACT_SHA256),$(LYRIQ_STOCK_IMS_CONTRACT_SHA256))
$(error Lyriq production stamp belongs to another stock IMS contract)
endif
ifneq ($(LYRIQ_GATE_APP_CLIENTS_CONTRACT_SHA256),$(LYRIQ_APP_CLIENTS_CONTRACT_SHA256))
$(error Lyriq production stamp belongs to another app-client contract)
endif
