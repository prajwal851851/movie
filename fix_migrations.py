import sqlite3
import os

db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tables to drop because they depend on the old architecture
    tables_to_drop = [
        'django_admin_log',
        'auth_user_groups',
        'auth_user_user_permissions',
        'auth_permission',
        'auth_group_permissions',
        'auth_group',
        'auth_user',
        'django_content_type',
        'django_session'
    ]
    
    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE {table};")
            print(f"Dropped table: {table}")
        except Exception as e:
            print(f"Could not drop {table}: {e}")
            
    # Clear migration history for system apps
    apps_to_clear = ['admin', 'auth', 'contenttypes', 'sessions']
    for app in apps_to_clear:
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = ?;", (app,))
            print(f"Cleared migration history for app: {app}")
        except Exception as e:
            print(f"Could not clear migration for {app}: {e}")
            
    conn.commit()
    conn.close()
else:
    print("Database not found")
