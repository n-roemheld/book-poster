from datetime import datetime, timezone


# Start date
# Only books read after this date are included  
start_date_year:         int = 2015 #2015
start_date_month:        int = 1#7
start_date_day:          int = 1#27
start_date = datetime(year=start_date_year, month=start_date_month, day=start_date_day, tzinfo=timezone.utc)
# End date
# Only books read before this date are included  
end_date_year:         int = datetime.today().year
end_date_month:        int = datetime.today().month
end_date_day:          int = datetime.today().day
end_date = datetime(year=end_date_year, month=end_date_month, day=end_date_day, tzinfo=timezone.utc)

title_str = f'Books read between {str(start_date.date())} {str(end_date.date())}'