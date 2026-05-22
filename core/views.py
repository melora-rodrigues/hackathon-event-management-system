from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Event, Submission, Evaluation,Notification, Team
from django.contrib import messages
import datetime,time  
from django.utils import timezone

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')
        
    is_organizer = request.user.groups.filter(name='Organizer').exists()
    is_judge = request.user.groups.filter(name='Judge').exists()
    is_participant = request.user.groups.filter(name='Participant').exists()
    
    if not is_organizer and not is_judge and not is_participant:
        return render(request, 'home.html', {
            'role_pending': True,
            'warning_message': "You are logged in, but you haven't been assigned a role yet. Please contact an administrator or enroll into the correct role."
        })
        
    if is_organizer:
        return redirect('organizer_dashboard')
    elif is_judge:
        return redirect('judge_dashboard')
    elif is_participant:  
        return redirect('participant_dashboard')

def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')

        if password1 != password2:
            return render(request, 'register.html',{'error': 'Passwords do not match!'})

        if len(password1) < 8:
            return render(request, 'register.html', {'error': 'Password must be at least 8 characters long!'})

        if role not in ['Participant', 'Judge', 'Organizer']:
            return render(request, 'register.html', {'error': 'Select a valid role'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})

        # pattern = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@$!%*?&]).{8,}$'
        # if not re.fullmatch(pattern, password):
        #     return render(request, 'register.html', {'error': 'Password must be strong! 8+ chars, uppercase, lowercase, number, special char.'})
        
        group = Group.objects.filter(name=role).first()

        if not group:
            return render(request, 'register.html', {'error': 'Role not found'})
        
        user = User.objects.create_user(
            first_name=first_name, 
            last_name=last_name,
            email=email,
            username=username, 
            password=password1
        )
        
        user.groups.add(group)
        return redirect('login')

    return render(request, 'register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.groups.filter(name='Organizer').exists():
                return redirect('organizer_dashboard')

            elif user.groups.filter(name='Judge').exists():
                return redirect('judge_dashboard')

            else:
                return redirect('participant_dashboard')

        else:
            return render(request, 'login.html', {
                'error': 'Invalid credentials'
            })

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def profile(request):
    user_role = "User"
    if request.user.groups.filter(name='Organizer').exists():
        user_role = "Organizer"
    elif request.user.groups.filter(name='Judge').exists():
        user_role = "Judge"
    elif request.user.groups.filter(name='Participant').exists():
        user_role = "Participant"

    return render(request, 'profile.html', {'user': request.user,'role': user_role})

@login_required
def create_event(request):
    if not request.user.groups.filter(name='Organizer').exists():
        return redirect('participant_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description','')
        date = request.POST.get('date')
        # submission_deadline = request.POST.get('submission_deadline')
        deadline_date = request.POST.get('submission_deadline')
        submission_deadline = datetime.combine(
            datetime.strptime(deadline_date, "%Y-%m-%d").date(),
            time(23, 59)
        )
        venue_or_link = request.POST.get('venue_or_link', '')
        event_type = request.POST.get('event_type') 

        if not name or not date or not submission_deadline:
            return render(request, 'create_event.html', {'error': 'Name, Date, and Submission Deadline are required!'})

        Event.objects.create(
            name=name,
            description=description,
            date=date,
            organizer=request.user,
            submission_deadline=submission_deadline,
            venue_or_link=venue_or_link,
            status='upcoming',
            event_type=event_type 
        )

        return redirect('organizer_dashboard')

    return render(request, 'create_event.html')

@login_required
def edit_event(request, event_id):
    if not request.user.groups.filter(name='Organizer').exists():
        return redirect('home')
    
    try:
        event = Event.objects.get(id=event_id, organizer=request.user)
    except Event.DoesNotExist:
        messages.error(request, "Event not found or you don't have permission to edit it.")
        return redirect('organizer_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        date = request.POST.get('date')
        submission_deadline = request.POST.get('submission_deadline')
        venue_or_link = request.POST.get('venue_or_link', '')

        if not name or not date or not submission_deadline:
            return render(request, 'edit_event.html', {'event': event, 'error': 'Name, Date, and Deadline are required!'})

        event.name = name
        event.description = description
        event.date = date
        event.submission_deadline = submission_deadline
        event.venue_or_link = venue_or_link
        event.save()
        
        messages.success(request, "Event updated successfully!")
        return redirect('organizer_dashboard')
        
    return render(request, 'edit_event.html', {'event': event})

def view_events(request):
    events = Event.objects.all()

    today = datetime.date.today()
    for event in events:
        if today < event.date:
            event.status = 'upcoming'   
        elif today == event.date:
            event.status = 'ongoing'    
        else:
            event.status = 'completed'  
        event.save()

    return render(request, 'view_events.html', {'events': events})



@login_required
def submit_project(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return redirect('view_events')

    if event.event_type == 'individual':

        existing = Submission.objects.filter(user=request.user,event=event).exists()

    else:

        try:
            team = Team.objects.get(leader=request.user,event=event)

        except Team.DoesNotExist:

            return render(request, 'submit_project.html', {
                'event': event,
                'error': 'Create a team first before submission.'
            })

        existing = Submission.objects.filter(
            team=team,
            event=event
        ).exists()

    # existing = Submission.objects.filter(user=request.user, event=event).exists()
    if existing:
        return render(request, 'submit_project.html', {
            'event': event,
            'error': 'You already submitted!'
        })

    if request.method == 'POST':
        # github_link = request.POST['github_link']
        github_link = request.POST.get('github_link', '')

        project_file = request.FILES.get('project_file')

        submission_status = 'Submitted'
        if timezone.now() > event.submission_deadline:
            submission_status = 'Late Submission'


        if event.event_type == 'individual':

            Submission.objects.create(
                user=request.user,
                event=event,
                github_link=github_link,
                project_file=project_file,
                status=submission_status
            )

        else:

            Submission.objects.create(
                team=team,
                event=event,
                github_link=github_link,
                project_file=project_file,
                status=submission_status
            )


        # Submission.objects.create(
        #     user=request.user,
        #     event=event,
        #     github_link=github_link,
        #     project_file=project_file,
        #     status=submission_status
        # )



        Notification.objects.create(
            user=request.user,
            title="Submission Confirmation",
            message=f"Your project for '{event.name}' has been received. Status: {submission_status}.")


        return redirect('participant_dashboard')

    return render(request, 'submit_project.html', {'event': event})


@login_required
def evaluate_project(request, submission_id):
    if not request.user.groups.filter(name='Judge').exists():
        messages.error(request, "Access denied.")
        return redirect('home')

    try:
        project = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return redirect('judge_dashboard')

    if request.method == 'POST':
        try:
            score_given = int(request.POST.get('score', 0)) 
        except(ValueError, TypeError):
            return render(request, 'evaluate_project.html', {
                'project': project,
                'error': 'Invalid score format. Please input a valid integer.'            })

        comments = request.POST.get('feedback', '')  

        if Evaluation.objects.filter(submission=project, judge=request.user).exists():
            return render(request, 'evaluate_project.html', {
                'project': project,
                'error': 'You already evaluated this project'
            })

        Evaluation.objects.create(
            submission=project,
            judge=request.user,
            score=score_given,
            feedback=comments
        )

        return redirect('judge_dashboard')

    return render(request, 'evaluate_project.html', {'project': project})

def reset_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if User.objects.filter(username=username).exists():
            if password1 == password2:
                user = User.objects.get(username=username)
                user.set_password(password1) 
                user.save()
            return redirect('login')
        else:
            return render(request, 'reset_password.html')
    return render(request, 'reset_password.html')

from django.contrib import messages  # Import Django's message framework

@login_required
def delete_event(request, event_id):
    if not request.user.groups.filter(name='Organizer').exists():
        return redirect('participant_dashboard')
        
    try:
        
        event = Event.objects.get(id=event_id, organizer=request.user)
        
        scores_exist = Evaluation.objects.filter(submission__event=event).exists()
        
        if scores_exist:
            messages.error(request, "Cannot delete event: Judges have already started scoring submissions.")
        else:
            event.delete()  
            messages.success(request, "Event successfully deleted.")
        
    except Event.DoesNotExist:
        messages.error(request, "Event not found or unauthorized.")
        
    return redirect('organizer_dashboard')

@login_required
def user_notifications(request):
    my_notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications.html', {'notifications': my_notifications})


def leaderboard(request, event_id):
    event = Event.objects.get(id=event_id)

    is_organizer = request.user.groups.filter(name='Organizer').exists()

    is_participant = request.user.groups.filter(name='Participant').exists()

    is_judge = request.user.groups.filter(name='Judge').exists()

    if is_judge:
        messages.error(request, "Access denied for judges.")
        return redirect('home')
    
    if is_organizer:
        pass

    elif is_participant:

        has_submitted = Submission.objects.filter(user=request.user,event=event).exists()

   
        if not has_submitted and event.status != "completed":
            return render(request, "leaderboard.html", {
                "event": event,
                "error": "Leaderboard will be visible after event completion."
            })

    if not (is_organizer or is_participant):
        messages.error(request, "Access denied.")
        return redirect('home')

    # try:
    #     event = Event.objects.get(id=event_id)
    # except Event.DoesNotExist:
    #     messages.error(request, "Event not found.")
    #     return redirect('view_events')

    submissions = Submission.objects.filter(event=event)
    leaderboard_list = []
    
    for sub in submissions:
        all_evaluations = sub.evaluation_set.all()
        
        total_score = 0
        judge_count = all_evaluations.count()
        
        for evaluation in all_evaluations:
            total_score = total_score + evaluation.score
            
        if judge_count > 0:
            average_score = total_score / judge_count
        else:
            average_score = 0
            
        project_data = {
            'submission': sub,
            'total_score': total_score,
            'average_score': round(average_score, 2),
            'judge_count': judge_count
        }
        leaderboard_list.append(project_data)
        
    # Sort from highest average score down to lowest
    leaderboard_list = sorted(leaderboard_list, key=lambda x: x['average_score'], reverse=True)
    
    # Add simple numbering rank positions
    rank_number = 1
    for item in leaderboard_list:
        item['rank'] = rank_number
        rank_number = rank_number + 1

    return render(request, 'leaderboard.html', {
        'event': event,
        'leaderboard': leaderboard_list
    })

@login_required
def organizer_dashboard(request):
    if not request.user.groups.filter(name='Organizer').exists():
        return redirect('home')
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'organizer_dashboard.html', {'events': events})



@login_required
def participant_dashboard(request):
    if not request.user.groups.filter(name='Participant').exists():
        messages.error(request, "Access denied. You must be enrolled as a Participant to view this dashboard.")
        return redirect('home')
    submissions = Submission.objects.filter(user=request.user)
    submission_data = []
    for submission in submissions:
        evals = submission.evaluation_set.all() 
        total = sum([e.score for e in evals])
        judge_count = evals.count() 
        submission_data.append({
            'submission': submission,
            'evaluations': evals,
            'total_score': total,
            'judge_count': judge_count
        })

    return render(request, 'participant_dashboard.html', {
        'submission_data': submission_data
    })



@login_required
def judge_dashboard(request):
    if not request.user.groups.filter(name='Judge').exists():
        messages.error(request, "Access denied. You must be a Judge to view this panel.")
        return redirect('home')  
    submissions = Submission.objects.all()
    return render(request, 'judge_dashboard.html', {
        'submissions': submissions
    })


