from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Create all sample data in the correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing data before creating new samples',
        )
        parser.add_argument(
            '--skip',
            nargs='+',
            choices=['groups', 'staff', 'metadata', 'courses', 'students', 'instructors', 'enrollments'],
            help='Skip specific data types (space separated)',
        )

    def handle(self, *args, **options):
        clear_flag = ['--clear'] if options['clear'] else []
        skip_list = options['skip'] or []
        
        commands_order = [
            ('groups', 'create_sample_groups'),
            ('staff', 'create_sample_staffs'),
            ('metadata', 'create_sample_metadatas'),
            ('courses', 'create_sample_courses'),
            ('students', 'create_sample_students'),
            ('instructors', 'create_sample_instructors'),
            ('enrollments', 'create_sample_enrollments'),
        ]

        self.stdout.write(self.style.SUCCESS('🚀 Starting sample data creation...'))
        
        for data_type, command_name in commands_order:
            if data_type in skip_list:
                self.stdout.write(self.style.WARNING(f'⏭️  Skipping {data_type}...'))
                continue
                
            self.stdout.write(self.style.SUCCESS(f'📦 Creating {data_type}...'))
            try:
                call_command(command_name, *clear_flag)
                self.stdout.write(self.style.SUCCESS(f'✅ {data_type.capitalize()} created successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to create {data_type}: {str(e)}'))
                # Decide whether to continue or stop on error
                continue
        
        self.stdout.write(self.style.SUCCESS('🎉 All sample data creation completed!'))
