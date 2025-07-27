from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.utils import send_notification
from notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Test WebSocket notifications functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-user',
            type=str,
            help='Username of the sender',
            required=True
        )
        parser.add_argument(
            '--to-user',
            type=str,
            help='Username of the recipient',
            required=True
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['Like', 'Comment', 'Follow Request', 'New Follower', 'Follow Accepted', 'Message'],
            default='Like',
            help='Type of notification to send'
        )

    def handle(self, *args, **options):
        try:
            from_user = User.objects.get(username=options['from_user'])
            to_user = User.objects.get(username=options['to_user'])
            
            notification = send_notification(
                actor=from_user,
                recipient=to_user,
                ntype=options['type'],
                extra_data={
                    'test': True,
                    'action_url': f'/profile/{from_user.slug}/'
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent {options["type"]} notification from {from_user.username} to {to_user.username}'
                )
            )
            
            # Show current unread count
            unread_count = Notification.objects.filter(recipient=to_user, read=False).count()
            self.stdout.write(f'Recipient now has {unread_count} unread notifications')
            
        except User.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'User not found: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending notification: {e}')
            )