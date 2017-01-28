#!/bin/bash

LOGPATH=/home/ubuntu/logs/worker.log
MANAGE=/home/ubuntu/code/campfin/manage.py

echo "`date`: Starting rebuild" >> $LOGPATH

source /home/ubuntu/.bash_profile
source /home/ubuntu/code/secrets/secrets.sh
source /home/ubuntu/.virtualenvs/campfin/bin/activate

OUTPUT=$( bash <<EOF
python $MANAGE scrape_pdc_races --year 2000 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2000 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2001 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2001 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2002 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2002 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2003 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2003 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2004 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2004 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2005 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2005 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2006 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2006 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2007 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2007 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2008 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2008 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2009 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2009 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2010 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2010 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2011 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2011 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2012 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2012 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2013 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2013 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2014 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2014 >> $LOGPATH

python $MANAGE scrape_pdc_races --year 2015 >> $LOGPATH
python $MANAGE scrape_pdc_disclosures --year 2015 >> $LOGPATH

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