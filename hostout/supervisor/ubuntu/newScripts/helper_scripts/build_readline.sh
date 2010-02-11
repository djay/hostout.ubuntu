# Install readline if required
#
# $LastChangedDate$ $LastChangedRevision$

if [ "X$INSTALL_READLINE" = "Xlocal" ] && [ ! -e "$LOCAL_HOME/lib/libreadline.a" ]
then
	echo "Compiling and installing readline local libraries ..."

	mkdir "$LOCAL_HOME/lib" >> $INSTALL_LOG 2>&1
	mkdir "$LOCAL_HOME/bin" >> $INSTALL_LOG 2>&1
	mkdir "$LOCAL_HOME/include" >> $INSTALL_LOG 2>&1
	mkdir "$LOCAL_HOME/man" >> $INSTALL_LOG 2>&1
	mkdir "$LOCAL_HOME/man/man1" >> $INSTALL_LOG 2>&1
	
	cd "$PKG"
	untar "$READLINE_TB"
	chmod -R 775 "$READLINE_DIR"
	cd "$READLINE_DIR"
	if [ "x$UNIVERSALSDK" != "x" ];	then
        CFLAGS="-fPIC -isysroot $UNIVERSALSDK -arch ppc -arch i386 -Wl,-syslibroot,$UNIVERSALSDK"
    else
        CFLAGS='-fPIC'
    fi
  	./configure CFLAGS="$CFLAGS" \
  	  --disable-shared \
  	  --prefix="$LOCAL_HOME" >> $INSTALL_LOG 2>&1
	"$GNU_MAKE" >> $INSTALL_LOG 2>&1
	"$GNU_MAKE" install >> $INSTALL_LOG 2>&1

	if [ ! -e "$LOCAL_HOME/lib/libreadline.a" ]
	then
		echo "Local install of readline has failed"
		seelog
		exit 1
	fi

	cd $PKG
	if [ -d "$READLINE_DIR" ]
	then
	        rm -rf "$READLINE_DIR"
	fi
else
	echo "Skipping readline compile/install"
fi

cd $CWD