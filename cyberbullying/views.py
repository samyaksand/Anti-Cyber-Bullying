from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Complaint
from .forms import ComplaintForm

# Create your views here.

def home(request):
    total_issues = Complaint.objects.all().count()
    resolved_issues = Complaint.objects.filter(resolution_status=True).count()
    args = {
        'total_issues' : total_issues,
        'resolved_issues' : resolved_issues
    }
    return render(request, 'cyberbullying/home.html', args)

@login_required(login_url='/admin/login/')
def admin_console(request):
    complaints = Complaint.objects.all().order_by('-created_date')
    args = {
        'complaints': complaints,
    }
    return render(request, 'cyberbullying/admin_console.html', args)

@login_required(login_url='/admin/login/')
def admin_console_resolved(request):
    complaints = Complaint.objects.filter(resolution_status=True).order_by('-created_date')
    args = {
        'complaints': complaints,
    }
    return render(request, 'cyberbullying/admin_console.html', args)

@login_required(login_url='/admin/login/')
def admin_console_unresolved(request):
    complaints = Complaint.objects.filter(resolution_status=False).order_by('-created_date')
    args = {
        'complaints': complaints,
    }
    return render(request, 'cyberbullying/admin_console.html', args)

@login_required(login_url='/admin/login/')
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    args = {
        'complaint' : complaint,
    }

    return render(request, 'cyberbullying/complaint_detail.html', args)

def complaint_new(request):
    form = ComplaintForm()
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.created_date = timezone.now()
            complaint.save()
            html = "<html><body>Your complaint has been registered. Go to <a href='/'>home.</a></body></html>"
            return HttpResponse(html)
    else:
        form = ComplaintForm()
    args = {
        'form': form,
    }
    return render(request, 'cyberbullying/complaint.html', args)
