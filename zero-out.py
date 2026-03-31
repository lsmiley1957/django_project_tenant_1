import os
import sys
import django
import psycopg2
from pathlib import Path

# 1. SETUP PATHS
# Get the absolute path of the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Add the project root to the python path
sys.path.append(str(BASE_DIR))

# 2. CONFIGURE DJANGO SETTINGS
# Based on your error, Django is looking for 'django_project_tenant_1.settings'
# Change the string below if your settings file is located elsewhere
# (e.g., 'core.settings' or 'myproject.settings')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')


def zero_out_migrations():
    try:
        # Initialize Django to access settings
        django.setup()
        from django.conf import settings

        db_conf = settings.DATABASES['default']

        print(f"Connecting to database: {db_conf['NAME']}...")

        conn = psycopg2.connect(
            dbname=db_conf['NAME'],
            user=db_conf['USER'],
            password=db_conf['PASSWORD'],
            host=db_conf.get('HOST', 'localhost'),
            port=db_conf.get('PORT', '5432')
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Step 1: Clear the django_migrations table
        # This tells Django that NO migrations have been run yet.
        print("Emptying django_migrations table...")
        cur.execute("TRUNCATE django_migrations CASCADE;")

        # Step 2: Clear tenant-specific migration tracking if it exists
        # django-tenants often tracks things in the public schema
        print("Ensuring public schema migration history is cleared...")
        cur.execute("DELETE FROM django_migrations WHERE app IS NOT NULL;")

        print("\nSuccess! The migration history has been zeroed out.")
        print("Now run these commands in your terminal:")
        print("1. python manage.py migrate_schemas --shared")
        print("2. python manage.py migrate_schemas --tenant")

        cur.close()
        conn.close()

    except ModuleNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Django could not find your settings module.")
        print(f"Check that the folder name containing 'settings.py' matches the one in this script.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    zero_out_migrations()