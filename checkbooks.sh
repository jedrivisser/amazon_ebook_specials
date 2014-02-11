#!/bin/bash
unset {http,ftp,all,socks,https}_proxy
unset {HTTP,FTP,ALL,SOCKS,HTTPS}_PROXY
/usr/bin/python ./ebook.py | /usr/bin/mail -s "book specials" jedri@jedrivisser.com
