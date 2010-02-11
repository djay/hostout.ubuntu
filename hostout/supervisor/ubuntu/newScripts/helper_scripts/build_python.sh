######################################
# Build Python (with readline and zlib support)
# note: Install readline and zlib before running this script
#
# $LastChangedDate$ $LastChangedRevision$

#Partial list of symbol deps...
# $PKG - location for building packages



echo "Installing Python $PYTHON_VERSION. This takes a while..."
cd "$PKG"
untar "$PYTHON_TB"
chmod -R 775 "$PYTHON_DIR"
cd "$PYTHON_DIR"

if [ "x$UNIVERSALSDK" != "x" ];	then
    EXFLAGS="--enable-universalsdk=$UNIVERSALSDK"
fi

if [ $NEED_LOCAL -eq 1 ]; then
	./configure $EXFLAGS \
		--prefix="$PY_HOME" \
		--with-readline \
		--with-zlib \
		--disable-tk \
		--with-gcc="$GCC -I\"$LOCAL_HOME\"/include" \
		--with-cxx="$GPP -I\"$LOCAL_HOME\"/include" \
		LDFLAGS="-L\"$LOCAL_HOME\"/lib" \
		>> "$INSTALL_LOG" 2>&1
else
    ./configure $EXFLAGS \
		--prefix="$PY_HOME" \
		--with-readline \
		--with-zlib \
		--disable-tk \
		--with-gcc="$GCC" \
		--with-cxx="$GPP" \
		>> $INSTALL_LOG 2>&1
fi
"$GNU_MAKE" >> $INSTALL_LOG 2>&1
"$GNU_MAKE" install >> $INSTALL_LOG 2>&1
cd "$PKG"
if [ -d "$PYTHON_DIR" ]
then
    rm -rf "$PYTHON_DIR"
fi
if [ ! -x "$PY_HOME/bin/python" ]
then
	echo "Install of Python $PYTHON_VERSION has failed."
	seelog
    exit 1
fi
"$PY_HOME/bin/python" -c "'test'.encode('zip')"
if [ $? -gt 0 ]
then
	echo "Python zlib support is missing; something went wrong in the zlib or python build."
	seelog
	exit 1
fi

cd "$CWD"
