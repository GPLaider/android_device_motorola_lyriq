# SPDX-FileCopyrightText: 2026 The OSverflow Project
# SPDX-License-Identifier: Apache-2.0

PRODUCT_SOONG_NAMESPACES += device/motorola/lyriq
PRODUCT_PACKAGE_OVERLAYS += device/motorola/lyriq/overlay
DEVICE_PACKAGE_OVERLAYS += device/motorola/lyriq/overlay-lineage

PRODUCT_PRODUCT_PROPERTIES += \
    bluetooth.profile.a2dp.source.enabled=true \
    bluetooth.profile.avrcp.target.enabled=true \
    bluetooth.profile.bas.client.enabled=true \
    bluetooth.profile.hfp.ag.enabled=true \
    bluetooth.profile.hid.host.enabled=true \
    bluetooth.profile.map.server.enabled=true \
    bluetooth.profile.opp.enabled=true \
    bluetooth.profile.pan.nap.enabled=true \
    bluetooth.profile.pan.panu.enabled=true \
    bluetooth.profile.pbap.server.enabled=true

PRODUCT_SYSTEM_PROPERTIES += \
    ro.telephony.default_network=26,26 \
    persist.device_config.mglru_native.lru_gen_config=none

PRODUCT_VENDOR_PROPERTIES += \
    persist.vendor.mtk.volte.enable=1 \
    persist.vendor.radio.volte_state=1

PRODUCT_COPY_FILES += \
    device/motorola/lyriq/rootdir/init.lyriq.compaction.rc:$(TARGET_COPY_OUT_SYSTEM)/etc/init/init.lyriq.compaction.rc \
    frameworks/native/data/etc/android.hardware.telephony.euicc.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/android.hardware.telephony.euicc.xml \
    device/motorola/lyriq/configs/osverflow/compatibility_profiles.properties:$(TARGET_COPY_OUT_SYSTEM)/etc/osverflow/compatibility_profiles.properties \
    device/motorola/lyriq/rootdir/.mountpoint:$(TARGET_COPY_OUT_ROOT)/metadata/.mountpoint \
    device/motorola/lyriq/rootdir/.mountpoint:$(TARGET_COPY_OUT_ROOT)/acct/.mountpoint

PRODUCT_USE_DYNAMIC_PARTITIONS := true
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    vendor_boot \
    dtbo \
    vbmeta \
    vbmeta_system \
    product \
    system \
    system_ext \
    vendor \
    vendor_dlkm \
    system_dlkm

PRODUCT_PACKAGES += \
    update_engine \
    update_verifier \
    android.hidl.allocator@1.0-service \
    EuiccGoogle \
    EuiccPartnerApp \
    lyriq_stock_euicc_privapp_permissions \
    lyriq_stock_euicc_default_permissions \
    OSverflowLyriqDozeOverlay

DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += \
    device/motorola/lyriq/vintf/compatibility_matrix.lyriq.xml

# Native Contextual Search provider and Launcher home/handle entrypoints.
PRODUCT_PACKAGES += OSverflowLyriqContextualSearchOverlay
PRODUCT_COPY_FILES += \
    device/motorola/lyriq/configs/com.google.android.feature.CONTEXTUAL_SEARCH.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/com.google.android.feature.CONTEXTUAL_SEARCH.xml
