import io

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile
from chatapp.models import Conversation, Message
from complaints.models import Complaint, Evidence
from incidents.models import IncidentEntry


DEMO_USERNAME_PREFIX = 'demo_'


class Command(BaseCommand):
    help = 'Creates realistic sample complaints, evidence and chat conversations for dashboard demonstration.'

    def handle(self, *args, **options):
        if Complaint.objects.filter(reporter_name__startswith='[demo]').exists():
            self.stdout.write('Demo data already present, skipping.')
            return

        reporters = [
            ('Priya Sharma', 'priya.sharma'),
            ('Rohan Mehta', 'rohan.mehta'),
            ('Ananya Iyer', 'ananya.iyer'),
            ('Vikram Nair', 'vikram.nair'),
            ('Fatima Khan', 'fatima.khan'),
        ]

        users = {}
        for display_name, slug in reporters:
            username = DEMO_USERNAME_PREFIX + slug
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'first_name': display_name.split()[0], 'last_name': display_name.split()[-1],
                          'email': slug.replace('.', '') + '@example.com'},
            )
            Profile.objects.get_or_create(user=user, defaults={'role': 'user'})
            users[display_name] = user

        complaint_specs = [
            {
                'reporter': 'Priya Sharma',
                'category': 'harassment',
                'platform': 'Instagram',
                'status': 'under_review',
                'description': 'Receiving repeated threatening messages on Instagram after a disagreement in a '
                                'group chat. The same account keeps creating new profiles after being blocked.',
                'notes': 'Contacted the reporter for additional screenshots of the newest accounts.',
                'evidence': True,
            },
            {
                'reporter': 'Rohan Mehta',
                'category': 'cyberbullying',
                'platform': 'WhatsApp',
                'status': 'in_progress',
                'description': 'A group of classmates added me to a WhatsApp group created only to mock and '
                                'insult me, sharing edited photos without consent.',
                'notes': 'Reviewing submitted chat export, identifying the group admin.',
                'evidence': True,
            },
            {
                'reporter': 'Ananya Iyer',
                'category': 'stalking',
                'platform': 'Facebook',
                'status': 'submitted',
                'description': 'A former acquaintance keeps tracking my location through mutual friends and shows '
                                'up at places I mention publicly on Facebook.',
                'notes': '',
                'evidence': False,
            },
            {
                'reporter': 'Vikram Nair',
                'category': 'threats',
                'platform': 'Discord',
                'status': 'resolved',
                'description': 'Received direct threats of violence in a gaming Discord server after a ranked '
                                'match dispute. Reported the user and left the server.',
                'notes': 'Platform moderation confirmed a permanent ban on the reported account. Case closed with '
                         'the reporter informed of the outcome.',
                'evidence': True,
            },
            {
                'reporter': 'Fatima Khan',
                'category': 'impersonation',
                'platform': 'Instagram',
                'status': 'info_required',
                'description': 'Someone created a duplicate Instagram profile using my photos and is messaging my '
                                'contacts pretending to be me asking for money.',
                'notes': 'Asked the reporter for the impersonating profile handle and any screenshots of the '
                         'messages sent to her contacts.',
                'evidence': False,
            },
            {
                'reporter': 'Priya Sharma',
                'category': 'doxxing',
                'platform': 'Twitter',
                'status': 'closed',
                'description': 'My home address and phone number were posted publicly in a thread after an '
                                'argument, and strangers started calling my phone.',
                'notes': 'Content was removed by the platform. Reporter confirmed no further contact attempts; '
                         'case closed.',
                'evidence': False,
            },
            {
                'reporter': 'Rohan Mehta',
                'category': 'hate_speech',
                'platform': 'YouTube',
                'status': 'under_review',
                'description': 'Comment section under a video I posted is filled with hateful remarks targeting my '
                                'community, with several comments encouraging others to pile on.',
                'notes': '',
                'evidence': False,
            },
            {
                'reporter': 'Ananya Iyer',
                'category': 'blackmail',
                'platform': 'Telegram',
                'status': 'in_progress',
                'description': 'Someone is threatening to share private photos unless I pay them, contacting me '
                                'repeatedly through a new Telegram account each time I block the previous one.',
                'notes': 'Advised the reporter not to make any payment. Collecting account handles for platform '
                         'escalation.',
                'evidence': True,
            },
        ]

        created_complaints = []
        for spec in complaint_specs:
            reporter_user = users[spec['reporter']]
            complaint = Complaint.objects.create(
                reporter=reporter_user,
                reporter_name='[demo] ' + spec['reporter'],
                category=spec['category'],
                platform=spec['platform'],
                description=spec['description'],
                investigation_notes=spec['notes'],
                contact_email=reporter_user.email,
            )
            complaint.status = spec['status']
            complaint.save()
            created_complaints.append((complaint, spec))

            IncidentEntry.objects.create(
                complaint=complaint,
                occurred_at=timezone.now(),
                platform=spec['platform'],
                description='Initial incident: ' + spec['description'][:140],
            )

            if spec['evidence']:
                text_content = (
                    'Sample evidence file for demonstration purposes.\n'
                    'This is a synthetic placeholder, not a real conversation.\n\n'
                    '[11:02] user: please stop messaging me\n'
                    '[11:03] unknown: you cannot avoid this forever\n'
                    '[11:05] user: I am reporting this conversation\n'
                )
                evidence = Evidence(
                    complaint=complaint,
                    uploaded_by=reporter_user,
                )
                evidence.file.save(
                    'sample_evidence.txt',
                    ContentFile(text_content.encode('utf-8')),
                    save=True,
                )

                try:
                    from PIL import Image, ImageDraw
                    img = Image.new('RGB', (480, 270), color=(28, 28, 28))
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([20, 20, 460, 250], outline=(229, 71, 75), width=3)
                    draw.text((40, 110), 'Sample screenshot placeholder', fill=(255, 255, 255))
                    draw.text((40, 140), 'Generated for demonstration only', fill=(242, 163, 165))
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    image_evidence = Evidence(complaint=complaint, uploaded_by=reporter_user)
                    image_evidence.file.save(
                        'sample_screenshot.png',
                        ContentFile(buffer.getvalue()),
                        save=True,
                    )
                except ImportError:
                    pass

        conversation_specs = [
            {
                'reporter': 'Priya Sharma',
                'exchange': [
                    (False, 'Hello, I submitted a complaint about repeated harassment on Instagram. Can someone look into it soon?'),
                    (True, 'Hello Priya, thank you for reaching out. I am reviewing your case now. Could you share the username of the newest account that contacted you?'),
                    (False, 'Yes, it is called "user_restart_22", created right after I blocked the last one.'),
                ],
            },
            {
                'reporter': 'Rohan Mehta',
                'exchange': [
                    (False, 'I uploaded the chat export for the group that was mocking me. Is that enough to proceed?'),
                    (True, 'Received it, thank you. We are identifying the group admin now and will update your case status shortly.'),
                ],
            },
            {
                'reporter': 'Fatima Khan',
                'exchange': [
                    (False, 'Someone is impersonating me and messaging my contacts for money. What should I do right now?'),
                    (True, 'First, please do not engage with the impersonating account. Could you send the exact profile handle so we can escalate it to the platform?'),
                    (False, 'It is "fatima.khan.real2024", I will send a screenshot of the messages too.'),
                ],
            },
        ]

        for spec in conversation_specs:
            reporter_user = users[spec['reporter']]
            conversation, _ = Conversation.objects.get_or_create(user=reporter_user)
            matching_complaint = next(
                (c for c, s in created_complaints if s['reporter'] == spec['reporter']), None
            )
            if matching_complaint and not conversation.complaint_id:
                conversation.complaint = matching_complaint
                conversation.save()
            for is_from_admin, body in spec['exchange']:
                Message.objects.create(
                    conversation=conversation,
                    is_from_admin=is_from_admin,
                    body=body,
                )

        self.stdout.write(self.style.SUCCESS(
            'Created %d demo complaints and %d demo conversations.' % (
                len(created_complaints), len(conversation_specs)
            )
        ))
