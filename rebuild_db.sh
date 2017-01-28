#!/bin/bash

LOGPATH=/home/ubuntu/logs/worker.log
MANAGE=/home/ubuntu/code/campfin/manage.py

echo "`date`: Starting rebuild" >> $LOGPATH

source /home/ubuntu/.bash_profile
source /home/ubuntu/code/secrets/secrets.sh
source /home/ubuntu/.virtualenvs/campfin/bin/activate

OUTPUT=$( bash <<EOF
python $MANAGE scrape_pdc_races --year 2016 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2016 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2017 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2017 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2018 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2018 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2019 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2019 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2020 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2020 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2021 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2021 >> $LOGPATH
EOF
)

echo "$OUTPUT" >> $LOGPATH
echo "`date`: Ending rebuild" >> $LOGPATH

echo "`date`: Beginning index rebuild" >> $LOGPATH
python $MANAGE update_index
echo "`date`: Ending index rebuild" >> $LOGPATH