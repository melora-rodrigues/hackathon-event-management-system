from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Event(models.Model):

    EVENT_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('team', 'Team'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    date = models.DateField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='individual'
    )

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]
    submission_deadline = models.DateTimeField()
    venue_or_link = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    
    def __str__(self):
        return self.name

class Team(models.Model):

    name = models.CharField(max_length=255)

    leader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='led_teams'
    )

    members = models.ManyToManyField(
        User,
        related_name='teams'
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

class Submission(models.Model):

  
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
      
    team = models.ForeignKey(Team,on_delete=models.CASCADE,null=True,blank=True)

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    github_link = models.URLField(max_length=500)

    project_file = models.FileField(upload_to='submissions/', blank=True, null=True) 
    status = models.CharField(max_length=50, default='Submitted')

    def __str__(self):

        if self.team:
            return f"{self.team.name} - {self.event.name}"

        return f"{self.user.username} - {self.event.name}"


class Evaluation(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='evaluation_set')
    judge = models.ForeignKey(User, on_delete=models.CASCADE)
    
    score = models.IntegerField(
        validators=[
            MinValueValidator(0),   
            MaxValueValidator(100)  
        ]
    ) 
    
    feedback = models.TextField(blank=True, default='')

    def __str__(self):

        if self.submission.team:
            return f"Score: {self.score} for {self.submission.team.name}"

        return f"Score: {self.score} for {self.submission.user.username}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Target recipient
    title = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return f"Alert for {self.user.username}: {self.title}"

def clean(self):
        if self.user and self.team:
            raise ValidationError("Submission cannot have both user and team.")
        if not self.user and not self.team:
            raise ValidationError("Submission must have either user or team.")

        def __str__(self):
            if self.team:
                return f"{self.team.name} - {self.event.name}"
            return f"{self.user.username} - {self.event.name}"
# class JudgeAssignment(models.Model):
#     submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
#     judge = models.ForeignKey(User, on_delete=models.CASCADE)

#     def __str__(self):
#         return f"Judge: {self.judge.username} assigned to review {self.submission.user.username}'s project"