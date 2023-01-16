#!/bin/bash
 
# create snappy and python binding with snappy- workaround for hanging in terminal 
/usr/local/snap/bin/snappy-conf /usr/bin/python3 | while read -r line; do
    echo "$line"
    [ "$line" = "or copy the 'snappy' module into your Python's 'site-packages' directory." ] && sleep 2 && pkill -TERM -f "snap/jre/bin/java"
done
