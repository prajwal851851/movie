# Generated migration to remove series fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streaming', '0005_movie_episodes_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='episodes_data',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='episode_number',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='episode_title',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='is_series',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='season_number',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='series_imdb_id',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='series_name',
        ),
    ]
