echo "Beginning to load lobbyist data"
time python manage.py load_pdc_lobbyists --flush
time python manage.py load_pdc_lobbyist_employers --flush
time python manage.py load_pdc_lobbyist_bio --flush
time python manage.py load_pdc_lobbying_firms --flush
time python manage.py load_pdc_lobbyist_monthly_expenses --flush
echo "Done loading lobbyist data"