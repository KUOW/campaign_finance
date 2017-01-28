#!/bin/bash

LOGPATH=/home/ubuntu/logs/worker.log
MANAGE=/home/ubuntu/code/campfin/manage.py

echo "`date`: Starting email notifications" >> $LOGPATH

source /home/ubuntu/.bash_profile
source /home/ubuntu/code/secrets/secrets.sh
source /home/ubuntu/.virtualenvs/campfin/bin/activate

OUTPUT=$( bash <<EOF
python $MANAGE email_report_recent_filings >> $LOGPATH

EOF
)

echo "$OUTPUT" >> $LOGPATH
echo "`date`: Ending email notifications" >> $LOGPATH
