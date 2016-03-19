if ENABLE_DRIVER_KERNEL
    MAYBE_KERNEL = 99-gnome15-kernel.rules
endif

if ENABLE_DRIVER_G19DIRECT
    MAYBE_G19DIRECT = 99-gnome15-g19direct.rules
endif

if ENABLE_DRIVER_G15DIRECT
    MAYBE_G15DIRECT = 99-gnome15-g15direct.rules
endif

if ENABLE_DRIVER_G930
    MAYBE_G930 = 99-gnome15-g930.rules
endif

if ENABLE_UDEV_RULES_PREFIX
    UDEV_RULES_PREFIX = $(prefix)
else
    UDEV_RULES_PREFIX =
endif
udevdir = $(UDEV_RULES_PREFIX)/lib/udev/rules.d

udev_DATA = 98-gnome15.rules $(MAYBE_KERNEL) $(MAYBE_G19DIRECT) $(MAYBE_G15DIRECT) $(MAYBE_G930)

EXTRA_DIST = 98-gnome15.rules 99-gnome15-g19direct.rules 99-gnome15-kernel.rules 99-gnome15-g15direct.rules 99-gnome15-g930.rules
