# streaming/management/commands/add_vidsrc_links.py
"""
Management command to add VidSrc streaming links to existing movies
Uses IMDb IDs from existing movies to generate VidSrc embed URLs
"""
from django.core.management.base import BaseCommand
from streaming.models import Movie, StreamingLink
import re


class Command(BaseCommand):
    help = 'Add VidSrc streaming links to existing movies using their IMDb IDs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of movies to process (for testing)'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode - show what would be done without saving'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-add VidSrc links even if they already exist'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        test_mode = options['test']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('🎬 VidSrc Link Generator'))
        self.stdout.write('='*70)
        
        # Get all movies with IMDb IDs
        movies = Movie.objects.exclude(imdb_id__isnull=True).exclude(imdb_id='')
        
        if limit:
            movies = movies[:limit]
            self.stdout.write(f'📊 Processing {limit} movies (test limit)')
        else:
            self.stdout.write(f'📊 Processing {movies.count()} movies')
        
        if test_mode:
            self.stdout.write(self.style.WARNING('⚠️  TEST MODE - No changes will be saved'))
        
        stats = {
            'processed': 0,
            'added': 0,
            'skipped_existing': 0,
            'skipped_invalid': 0,
            'errors': 0
        }

        for movie in movies:
            stats['processed'] += 1
            
            try:
                # Extract clean IMDb ID
                imdb_id = self.extract_imdb_id(movie.imdb_id)
                
                if not imdb_id:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  [{stats["processed"]}] {movie.title}: Invalid IMDb ID format')
                    )
                    stats['skipped_invalid'] += 1
                    continue
                
                # Check if VidSrc link already exists
                if not force and StreamingLink.objects.filter(
                    movie=movie, 
                    server_name='VidSrc'
                ).exists():
                    stats['skipped_existing'] += 1
                    continue
                
                # Generate VidSrc URL
                vidsrc_url = f'https://vidsrc.to/embed/movie/{imdb_id}'
                
                if test_mode:
                    self.stdout.write(
                        f'✓ [{stats["processed"]}] {movie.title} ({movie.year})\n'
                        f'   IMDb: {imdb_id}\n'
                        f'   VidSrc: {vidsrc_url}'
                    )
                    stats['added'] += 1
                else:
                    # Delete existing VidSrc link if force mode
                    if force:
                        StreamingLink.objects.filter(
                            movie=movie,
                            server_name='VidSrc'
                        ).delete()
                    
                    # Create VidSrc streaming link
                    StreamingLink.objects.create(
                        movie=movie,
                        stream_url=vidsrc_url,
                        server_name='VidSrc',
                        quality='HD',
                        language='EN',
                        is_active=True
                    )
                    
                    stats['added'] += 1
                    
                    if stats['added'] % 100 == 0:
                        self.stdout.write(f'✓ Added {stats["added"]} VidSrc links...')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {movie.title}: {str(e)}')
                )
                stats['errors'] += 1
        
        # Print summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('='*70)
        self.stdout.write(f'Movies Processed:     {stats["processed"]}')
        self.stdout.write(self.style.SUCCESS(f'✓ VidSrc Links Added: {stats["added"]}'))
        self.stdout.write(f'⊘ Already Had VidSrc: {stats["skipped_existing"]}')
        self.stdout.write(f'⚠ Invalid IMDb IDs:   {stats["skipped_invalid"]}')
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors:            {stats["errors"]}'))
        
        self.stdout.write('='*70)
        
        if not test_mode and stats['added'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully added {stats["added"]} VidSrc streaming links!\n'
                    f'Users can now choose VidSrc as an alternative server.'
                )
            )
        elif test_mode:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Test mode completed. Run without --test to actually add links.'
                )
            )

    def extract_imdb_id(self, raw_id):
        """
        Extract clean IMDb ID from various formats
        Examples:
            'goojara_tt0133093' -> 'tt0133093'
            'tt0133093' -> 'tt0133093'
            '1flix_123456' -> None (not IMDb)
        """
        if not raw_id:
            return None
        
        # Look for IMDb ID pattern (tt followed by digits)
        match = re.search(r'(tt\d+)', raw_id)
        if match:
            return match.group(1)
        
        return None
