from story.models import Story
from core.models import Event

def expired_story():
    stories = Story.objects.all()
    events = Event.objects.all()
    for story in stories:
        if story.is_expired():
            story.delete()
    
    for event in events:
        if event.is_expired():
            event.delete()
    
    return None
