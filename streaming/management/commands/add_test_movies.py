# streaming/management/commands/add_test_movies.py
from django.core.management.base import BaseCommand
from streaming.models import Movie, StreamingLink

class Command(BaseCommand):
    help = 'Add test movies to the database'

    def handle(self, *args, **options):
        test_movies = [
            {
                'imdb_id': 'tt0111161',
                'title': 'The Shawshank Redemption',
                'year': 1994,
                'synopsis': 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_SX300.jpg',
                'source_url': 'https://example.com',
                'source_site': 'test',
                'stream_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'
            },
            {
                'imdb_id': 'tt0068646',
                'title': 'The Godfather',
                'year': 1972,
                'synopsis': 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
                'source_url': 'https://example.com',
                'source_site': 'test',
                'stream_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4'
            },
            {
                'imdb_id': 'tt0468569',
                'title': 'The Dark Knight',
                'year': 2008,
                'synopsis': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests.',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg',
                'source_url': 'https://example.com',
                'source_site': 'test',
                'stream_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'
            },
            {
                'imdb_id': 'tt0071562',
                'title': 'The Godfather Part II',
                'year': 1974,
                'synopsis': 'The early life and career of Vito Corleone in 1920s New York City is portrayed, while his son, Michael, expands and tightens his grip on the family crime syndicate.',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BMWMwMGQzZTItY2JlNC00OWZiLWIyMDctNDk2ZDQ2YjRjMWQ0XkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg',
                'source_url': 'https://example.com',
                'source_site': 'test',
                'stream_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4'
            },
            {
                'imdb_id': 'tt0050083',
                'title': '12 Angry Men',
                'year': 1957,
                'synopsis': 'A jury holdout attempts to prevent a miscarriage of justice by forcing his colleagues to reconsider the evidence.',
                'poster_url': 'https://m.media-amazon.com/images/M/MV5BMWU4N2FjNzYtNTVkNC00NzQ0LTg0MjAtYTJlMjFhNGUxZDFmXkEyXkFqcGdeQXVyNjc1NTYyMjg@._V1_SX300.jpg',
                'source_url': 'https://example.com',
                'source_site': 'test',
                'stream_url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4'
            }
        ]

        for movie_data in test_movies:
            stream_url = movie_data.pop('stream_url')
            
            movie, created = Movie.objects.update_or_create(
                imdb_id=movie_data['imdb_id'],
                defaults=movie_data
            )
            
            StreamingLink.objects.get_or_create(
                movie=movie,
                stream_url=stream_url,
                defaults={
                    'quality': 'HD',
                    'language': 'EN',
                    'is_active': True
                }
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} movie: {movie.title}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully added {len(test_movies)} test movies!')
        )