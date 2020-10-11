#!/usr/bin/env bash
#
# Script for migrating from epydoc to Sphinx style docstrings.
#
# WARNING: THIS SCRIPT MODIFIES FILES IN PLACE. BE SURE TO BACKUP THEM BEFORE
# RUNNING IT.

DIRECTORY=$1

SED=`which gsed gnused sed`

for value in $SED
do
    SED=${value}
    break
done

if [ ! $DIRECTORY ]; then
    echo "Usage: ./migrate_docstrings.sh <directory with your code>"
    exit 1
fi

OLD_VALUES[0]='@type'
OLD_VALUES[1]='@keyword'
OLD_VALUES[2]='@param'
OLD_VALUES[3]='@return'
OLD_VALUES[4]='@rtype'
OLD_VALUES[5]='L{\([^}]\+\)}'
OLD_VALUES[6]='C{\(int\|float\|str\|list\|tuple\|dict\|bool\|None\|generator\|object\)}'
OLD_VALUES[7]='@\(ivar\|cvar\|var\)'
OLD_VALUES[8]='I{\([^}]\+\)}'

NEW_VALUES[0]=':type'
NEW_VALUES[1]=':keyword'
NEW_VALUES[2]=':param'
NEW_VALUES[3]=':return'
NEW_VALUES[4]=':rtype'
NEW_VALUES[5]=':class:`\1`'
NEW_VALUES[6]='``\1``'
NEW_VALUES[7]=':\1'
NEW_VALUES[8]='``\1``'

for (( i = 0 ; i < ${#OLD_VALUES[@]} ; i++ ))
do
    old_value=${OLD_VALUES[$i]}
    new_value=${NEW_VALUES[$i]}

    cmd="find ${DIRECTORY} -name '*.py' -type f -print0 | xargs -0 ${SED} -i -e 's/${old_value}/${new_value}/g'"

    echo "Migrating: ${old_value} -> ${new_value}"
    eval "$cmd"
done
