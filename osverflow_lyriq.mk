# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, device/motorola/lyriq/device.mk)
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)

PRODUCT_PACKAGES += \
    ImsService \
    mediatek-carrier-config-manager \
    mediatek-common

PRODUCT_BOOT_JARS += \
    system_ext:mediatek-carrier-config-manager \
    system_ext:mediatek-common \
    system_ext:mediatek-ims-base

PRODUCT_SHIPPING_API_LEVEL := 33
PRODUCT_BUILD_VENDOR_BOOT_IMAGE := false
PRODUCT_VIRTUAL_AB_OTA := true
PRODUCT_BUILD_GENERIC_OTA_PACKAGE := true
PRODUCT_OTA_PUBLIC_KEYS := \
    device/motorola/lyriq/.local-signing/releasekey.x509.pem

PRODUCT_BRAND := motorola
PRODUCT_DEVICE := lyriq
PRODUCT_NAME := osverflow_lyriq
PRODUCT_MODEL := motorola edge 40
PRODUCT_MANUFACTURER := motorola
