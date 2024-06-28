from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from scrapping import search_website, send_email1

# Define the default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 29),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'website_search_and_email',
    default_args=default_args,
    description='Search a website and send email notification if new sale is found',
    schedule_interval=timedelta(days=1),
)

# Define tasks
search_task = PythonOperator(
    task_id='search_website_task',
    python_callable=search_website,
    dag=dag,
)

email_task = PythonOperator(
    task_id='send_email_task',
    python_callable=send_email1,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
search_task >> email_task
