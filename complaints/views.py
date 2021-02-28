from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from ratelimit.decorators import ratelimit
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CaseMessage, Complaint, Evidence, EvidenceVerification,
    VERIFICATION_RESULT_FAILED, VERIFICATION_RESULT_VERIFIED,
)
from .permissions import IsAdmin, IsOwnerOrAdmin, user_is_admin
from .serializers import (
    AdminComplaintUpdateSerializer,
    CaseMessageSerializer,
    ComplaintCreateSerializer,
    ComplaintDetailSerializer,
    ComplaintListSerializer,
    EvidenceSerializer,
    EvidenceVerificationSerializer,
)


def get_complaint_with_access_check(request, pk):
    """Looks up a complaint by pk and verifies the requester is allowed to
    read/act on it: the registered owner, an admin, or someone presenting
    the complaint's own tracking_code (the secret given to anonymous and
    registered reporters alike at submission time, not a guessable pk)."""
    complaint = get_object_or_404(Complaint, pk=pk)
    if user_is_admin(request.user):
        return complaint
    if request.user.is_authenticated and complaint.reporter_id == request.user.id:
        return complaint
    supplied_code = request.data.get('tracking_code') or request.query_params.get('tracking_code')
    if supplied_code and complaint.tracking_code == supplied_code:
        return complaint
    raise PermissionDenied('You do not have access to this complaint.')


class ComplaintCreateView(generics.CreateAPIView):
    serializer_class = ComplaintCreateSerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/h', block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        reporter = self.request.user if self.request.user.is_authenticated else None
        is_anonymous = serializer.validated_data.get('is_anonymous') or reporter is None
        serializer.save(reporter=reporter, is_anonymous=is_anonymous)


class MyComplaintListView(generics.ListAPIView):
    serializer_class = ComplaintListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Complaint.objects.filter(reporter=self.request.user)


class ComplaintDetailView(generics.RetrieveAPIView):
    serializer_class = ComplaintDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = Complaint.objects.all()


class TrackComplaintView(APIView):
    """Public, secure tracking lookup by reference ID + the email/owner used
    at submission time. Does not require registration."""
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key='ip', rate='20/h', block=True))
    def post(self, request):
        reference_id = request.data.get('reference_id', '').strip()
        email = request.data.get('email', '').strip().lower()
        if not reference_id or not email:
            return Response({'detail': 'reference_id and email are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            complaint = Complaint.objects.get(reference_id=reference_id)
        except Complaint.DoesNotExist:
            return Response({'detail': 'No matching complaint found.'}, status=status.HTTP_404_NOT_FOUND)

        owner_email = complaint.contact_email.lower() if complaint.contact_email else (
            complaint.reporter.email.lower() if complaint.reporter else ''
        )
        if owner_email != email:
            return Response({'detail': 'No matching complaint found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(ComplaintDetailSerializer(complaint, context={'request': request}).data)


class EvidenceUploadView(generics.CreateAPIView):
    """Requires proof of access to the complaint: ownership, admin status,
    or the complaint's tracking_code (for anonymous reporters), so evidence
    cannot be attached to an arbitrary complaint by guessing its pk."""
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        complaint = self._get_complaint()
        uploader = self.request.user if self.request.user.is_authenticated else None
        serializer.save(complaint=complaint, uploaded_by=uploader)

    def _get_complaint(self):
        return get_complaint_with_access_check(self.request, self.kwargs['pk'])


class CaseMessageListCreateView(generics.ListCreateAPIView):
    """Requires the same proof of access as EvidenceUploadView: ownership,
    admin status, or the complaint's tracking_code."""
    serializer_class = CaseMessageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        complaint = self._get_complaint()
        qs = complaint.case_messages.all()
        if not user_is_admin(self.request.user):
            qs = qs.filter(internal_note=False)
        return qs

    def perform_create(self, serializer):
        complaint = self._get_complaint()
        is_admin = user_is_admin(self.request.user)
        serializer.save(
            complaint=complaint,
            author_is_admin=is_admin,
            author_name=self.request.user.get_username() if is_admin else 'Reporter',
            internal_note=serializer.validated_data.get('internal_note', False) and is_admin,
        )

    def _get_complaint(self):
        return get_complaint_with_access_check(self.request, self.kwargs['pk'])


class AdminComplaintListView(generics.ListAPIView):
    serializer_class = ComplaintListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = Complaint.objects.all()
        status_filter = self.request.query_params.get('status')
        category_filter = self.request.query_params.get('category')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(category=category_filter)
        return qs


class AdminComplaintUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminComplaintUpdateSerializer
    permission_classes = [IsAdmin]
    queryset = Complaint.objects.all()


class EvidenceVerifyView(APIView):
    """Admin-triggered recalculation of an Evidence file's hash, compared
    against the hash recorded at upload time. Creates one append-only
    EvidenceVerification row per call and never mutates the Evidence record."""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404
        evidence = get_object_or_404(Evidence, pk=pk)

        computed_hash = evidence.recalculate_hash()
        result = (
            VERIFICATION_RESULT_VERIFIED if computed_hash == evidence.sha256_hash
            else VERIFICATION_RESULT_FAILED
        )
        verification = EvidenceVerification.objects.create(
            evidence=evidence,
            verified_by=request.user,
            computed_hash=computed_hash,
            result=result,
        )
        return Response(EvidenceVerificationSerializer(verification).data, status=status.HTTP_201_CREATED)


class EvidenceVerificationHistoryView(generics.ListAPIView):
    serializer_class = EvidenceVerificationSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return EvidenceVerification.objects.filter(evidence_id=self.kwargs['pk'])


def complaint_detail_page(request, pk):
    """Renders the complaint detail/case page: status, investigation notes,
    incident timeline, evidence list with an upload form, and the case
    message thread with a reply form. Reachable by the registered owner,
    an admin, or anyone presenting the correct tracking_code (the secret
    handed to anonymous and registered reporters alike at submission)."""
    complaint = get_object_or_404(Complaint, pk=pk)
    tracking_code = request.GET.get('tracking_code', '')
    is_admin = user_is_admin(request.user)
    is_owner = request.user.is_authenticated and complaint.reporter_id == request.user.id
    has_tracking_code = bool(tracking_code) and complaint.tracking_code == tracking_code

    if not (is_admin or is_owner or has_tracking_code):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('You do not have access to this complaint.')

    visible_messages = complaint.case_messages.all()
    if not is_admin:
        visible_messages = visible_messages.filter(internal_note=False)

    return render(request, 'complaints/detail.html', {
        'complaint': complaint,
        'tracking_code': tracking_code,
        'is_admin': is_admin,
        'messages_thread': visible_messages,
    })
