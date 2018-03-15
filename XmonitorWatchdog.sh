#!/bin/bash

declare -A mapper
conf=dog.pid


function debug
{
    echo $@
}

function watch
{
    local pid=$1
    local index=`ps -ef|awk '{print $2}'|grep -P "^${pid}$"`
    if [ "${index}None" = "None" ]; then
        echo gone
        return
    fi
    echo stay
}


function dogit
{
    while [ 1 ]
    do
        sleep 20
        for pid in ${!mapper[@]}
        do
            # debug pid:$pid
            local t=`watch $pid`
            # debug "test result is $t!!!"
            if [ "$t" = "gone" ]; then
                # debug "$c with pid $pid was gone"
                loadscript ${mapper[$pid]}
                unset mapper[$pid]
                sed -i "/$pid/d" $conf
            fi
        done
    done
}


function loadscript
{
    local script=$@
    # debug script=$script
    $script > /dev/null 2>&1 &
    local pid=$!
    mapper[$pid]=$script
    echo $pid >> $conf
}

function clean
{
    if [ -f $conf ]; then
        while read line; do
            if [ -n "$line" ]; then
                pid=`ps -ef|awk '{print $2}'|grep $line|grep -v 'grep'`
                if [ -n "${pid}" ]; then
                    # debug killing $pid
                    kill $pid
                fi
            fi
        done < $conf
    fi
    echo > $conf
    # debug done!
}

function main
{
    clean
    local file=$1
    # echo $file
    if [ -f $file ]; then
        while read line
        do
            loadscript $line
        done < $file
        dogit
    else
        echo "Not a file!"
    fi
}

cd $(dirname $0)
main $1;