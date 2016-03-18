SHELL = /bin/sh
top_srcdir = ..
# See README.md
build_dir = $(GNOME15_GIT)/build
LANG=C

MACROFILES= libtool.m4 ltoptions.m4 ltsugar.m4 ltversion.m4 lt~obsolete.m4

MAINTAINERCLEANFILES = \
	aclocal.m4 \
	compile \
	config.guess \
	config.sub \
	configure \
	depcomp \
	install-sh \
	ltmain.sh \
	missing \
	py-compile

init_dir:
	test ! -d $(build_dir) && mkdir -p $(build_dir) || echo "build_dir already present"

autoreconf_it:
	cd $(top_srcdir) && autoreconf -i

configure_it: init_dir
	cd $(build_dir) && $(top_srcdir)/configure --srcdir=$(top_srcdir)

uninstall_it:
	cd $(build_dir) && test -d "$(PREFIX_DIR)" && make uninstall || echo 'no need uninstall phase.'

clean_it: uninstall_it
	cd $(build_dir) && make clean

fullclean_it: clean_it
	cd $(build_dir) && make maintainer-clean
	cd $(top_srcdir) && rm -v $(MAINTAINERCLEANFILES)
	cd $(top_srcdir)/m4 && rm -v $(MACROFILES)
	find $(top_srcdir) -name 'Makefile.in' -delete
	cd $(build_dir) && find . -depth -type d -delete
	rmdir -v $(build_dir)
#	cd $(build_dir) && test -f *.tar.gz && rm -v *.tar.gz || echo 'archive not found.'

distcheck_it:
	cd $(build_dir) && make distcheck

