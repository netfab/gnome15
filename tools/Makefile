SHELL = /bin/sh
top_srcdir = ..
# See README.md
build_dir = $(GNOME15_GIT)/build
DESTDIR=/tmp/gnome15-inst
PREFIX_DIR=/usr
LANG=C

M4_FILES= libtool.m4 ltoptions.m4 ltsugar.m4 ltversion.m4 lt~obsolete.m4

AUX_FILES = \
	compile \
	config.guess \
	config.sub \
	depcomp \
	install-sh \
	ltmain.sh \
	missing \
	py-compile

TOP_FILES = \
	aclocal.m4 \
	configure

init_dir:
	test ! -d $(build_dir) && mkdir -p $(build_dir) || echo "build_dir already present"

autoreconf_it:
	cd $(top_srcdir) && autoreconf -i

configure_it: init_dir
	cd $(build_dir) && $(top_srcdir)/configure --prefix=$(PREFIX_DIR) --srcdir=$(top_srcdir) --disable-udev-rules-prefix

build_it:
	cd $(build_dir) && make

install_it:
	cd $(build_dir) && make DESTDIR=$(DESTDIR) install

uninstall_it:
	cd $(build_dir) && test -d "$(DESTDIR)" && make DESTDIR=$(DESTDIR) uninstall || echo 'no need uninstall phase.'

clean_it: uninstall_it
	cd $(build_dir) && make clean

fullclean_it: clean_it
	cd $(build_dir) && make maintainer-clean
	cd $(top_srcdir)/build-aux && rm -v $(AUX_FILES)
	rmdir -v $(top_srcdir)/build-aux
	cd $(top_srcdir)/m4 && rm -v $(M4_FILES)
	find $(top_srcdir) -name 'Makefile.in' -delete
	cd $(build_dir) && find . -depth -type d -delete
	cd $(build_dir) && test -f *.tar.gz && rm -v *.tar.gz || echo 'archive not found.'
	rmdir -v $(build_dir)
	cd $(top_srcdir) && rm -v $(TOP_FILES)

distcheck_it:
	cd $(build_dir) && make distcheck

