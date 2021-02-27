from django.shortcuts import render, get_object_or_404
from .models import Complaint

# Create your views here.

def home(request):
    total_issues = Complaint.objects.all().count()
    resolved_issues = Complaint.objects.filter(resolution_status=True).count()
    args = {
        'total_issues' : total_issues,
        'resolved_issues' : resolved_issues
    }
    return render(request, 'cyberbullying/home.html', args)

def admin_console(request):
    complaints = Complaint.objects.all().order_by('-created_date')
    args = {
        'complaints': complaints,
    }
    return render(request, 'cyberbullying/admin_console.html', args)

def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    args = {
        'complaint' : complaint,
    }

    return render(request, 'cyberbullying/complaint_detail.html', args)
