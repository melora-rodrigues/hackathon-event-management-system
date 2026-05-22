from django.contrib import admin
from .models import Event, Submission, Evaluation

# Register your models here.

admin.site.register(Event)
admin.site.register(Submission)
admin.site.register(Evaluation)
