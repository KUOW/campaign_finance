#!/bin/bash
source /home/ubuntu/.bash_profile
workon campfin

python /home/aepton/code/campfin/manage.py scrape_pdc_races
python /home/aepton/code/campfin/manage.py scrape_pdc_contributions