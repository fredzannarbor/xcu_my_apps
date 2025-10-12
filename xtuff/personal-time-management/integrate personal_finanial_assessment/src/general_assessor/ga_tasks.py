from celery import shared_task

@shared_task
def check_status():
    # Logic to check the status of the general assessor
    print('Checking status...')
    # Implement status checking logic here

@shared_task
def monthly_coverage_check():
    # Logic to perform a monthly coverage check
    print('Performing monthly coverage check...')
    # Implement coverage check logic here
