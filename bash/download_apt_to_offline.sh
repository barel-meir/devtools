#! /bin/bash

# global variables
APP=

function usage()
{
    echo -e "usage: [-a|--app] [-h|--help]"
    echo -e "        -a|--app   : specify the app you want to download."
    echo -e "        -h|--help  : show usage."
    exit
}

function clean_cache()
{
    sudo apt-get clean 
}

function download()
{
    echo "dwonload (only) $APP"
    sudo apt-get install --download-only $APP -y
}

function save_artifact()
{
    echo "saving artifact"
    cach_path=/var/cache/apt/archives
    artifact_name=$APP.tar.gz
    tar cvfz $artifact_name $cach_path
    echo "artifact saved: $artifact_name"
}

function main()
{
    while getopts "a:h" option
    do
        case "$option" in
            a)
                APP="$OPTARG"
                ;;
            h)
                usage
                ;;
        esac
    done

    if [ $OPTIND -eq 1 ]
    then
        usage
    fi

    clean_cache
    download
    save_artifact
}

main "$@"