from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone

from complaints.models import Complaint, STATUS_RESOLVED, STATUS_CLOSED
from .forms import ComplaintForm, ContactMessageForm


def home(request):
    total_issues = Complaint.objects.count()
    resolved_issues = Complaint.objects.filter(status__in=[STATUS_RESOLVED, STATUS_CLOSED]).count()
    return render(request, 'cyberbullying/home.html', {
        'total_issues': total_issues,
        'resolved_issues': resolved_issues,
    })


def about(request):
    return render(request, 'cyberbullying/about.html')


def complaint_new(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.reporter = request.user if request.user.is_authenticated else None
            if not complaint.is_anonymous and complaint.reporter is None and not complaint.contact_email:
                complaint.is_anonymous = True
            complaint.save()
            return render(request, 'cyberbullying/complaint_registered.html', {'complaint': complaint})
    else:
        form = ComplaintForm()
    return render(request, 'cyberbullying/complaint.html', {'form': form})


def track_complaint(request):
    complaint = None
    error = None
    reference_id = ''
    email = ''
    if request.method == 'POST':
        reference_id = request.POST.get('reference_id', '').strip()
        email = request.POST.get('email', '').strip().lower()
        try:
            candidate = Complaint.objects.get(reference_id=reference_id)
            owner_email = candidate.contact_email.lower() if candidate.contact_email else (
                candidate.reporter.email.lower() if candidate.reporter else ''
            )
            if owner_email == email:
                complaint = candidate
            else:
                error = 'No matching complaint found for that reference ID and email.'
        except Complaint.DoesNotExist:
            error = 'No matching complaint found for that reference ID and email.'
    return render(request, 'cyberbullying/track_complaint.html', {
        'complaint': complaint, 'error': error, 'reference_id': reference_id, 'email': email,
    })


def live_support(request):
    return render(request, 'cyberbullying/live_support.html')


def cyber_safety(request):
    return render(request, 'cyberbullying/cyber_safety.html')


def emergency(request):
    return render(request, 'cyberbullying/emergency.html')


def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you, your message has been received.')
        else:
            messages.error(request, 'Please provide a message before sending.')
        return redirect('contact')
    return render(request, 'cyberbullying/contact.html')
