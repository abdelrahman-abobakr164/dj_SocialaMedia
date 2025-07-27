from datetime import timedelta
from django.utils import timezone


def filter_notifications_by_date_range(queryset, date_range):
    today = timezone.now().date()

    if date_range == "today":
        return queryset.filter(created_at__date=today)
    elif date_range == "yesterday":
        yesterday = today - timedelta(days=1)
        return queryset.filter(created_at__date=yesterday)
    elif date_range == "last_30_days":
        thirty_days_ago = today - timedelta(days=30)
        return queryset.filter(created_at__date__gte=thirty_days_ago)
    else:
        return queryset.all()
