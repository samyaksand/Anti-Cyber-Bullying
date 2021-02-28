from rest_framework import serializers

from .models import CaseMessage, Complaint, Evidence, EvidenceVerification


class EvidenceVerificationSerializer(serializers.ModelSerializer):
    verified_by_display = serializers.CharField(source='verified_by.get_username', default='', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)

    class Meta:
        model = EvidenceVerification
        fields = [
            'id', 'computed_hash', 'result', 'result_display', 'verified_by_display', 'verified_at',
        ]
        read_only_fields = fields


class EvidenceSerializer(serializers.ModelSerializer):
    verifications = EvidenceVerificationSerializer(many=True, read_only=True)

    class Meta:
        model = Evidence
        fields = [
            'id', 'file', 'uploaded_at', 'sha256_hash', 'original_filename',
            'content_type', 'file_size', 'verifications',
        ]
        read_only_fields = [
            'uploaded_at', 'sha256_hash', 'original_filename', 'content_type',
            'file_size', 'verifications',
        ]


class CaseMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseMessage
        fields = ['id', 'author_is_admin', 'author_name', 'body', 'internal_note', 'created_at']
        read_only_fields = ['author_is_admin', 'created_at']


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            'reference_id', 'tracking_code', 'reporter_name', 'category', 'platform',
            'incident_date', 'description', 'urls', 'is_anonymous', 'contact_email',
        ]
        read_only_fields = ['reference_id', 'tracking_code']

    def validate(self, attrs):
        if attrs.get('is_anonymous') and not attrs.get('contact_email'):
            raise serializers.ValidationError(
                'An email is required for anonymous reports so case updates can be tracked.'
            )
        return attrs


class ComplaintDetailSerializer(serializers.ModelSerializer):
    evidence = EvidenceSerializer(many=True, read_only=True)
    case_messages = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'reference_id', 'tracking_code', 'is_anonymous', 'contact_email',
            'reporter_name', 'category', 'category_display', 'platform', 'incident_date',
            'description', 'urls', 'status', 'status_display', 'investigation_notes',
            'created_at', 'updated_at', 'resolved_at', 'evidence', 'case_messages',
        ]
        read_only_fields = [
            'reference_id', 'tracking_code', 'created_at', 'updated_at', 'resolved_at',
        ]

    def get_case_messages(self, obj):
        request = self.context.get('request')
        is_admin = request and request.user.is_authenticated and getattr(
            getattr(request.user, 'profile', None), 'is_admin', False
        )
        qs = obj.case_messages.all()
        if not is_admin:
            qs = qs.filter(internal_note=False)
        return CaseMessageSerializer(qs, many=True).data


class ComplaintListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'reference_id', 'category', 'category_display', 'status',
            'status_display', 'created_at', 'is_anonymous',
        ]


class AdminComplaintUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['status', 'investigation_notes', 'assigned_admin']
