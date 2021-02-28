from .models import Profile


def create_user_profile(backend, user, response, *args, **kwargs):
    profile, created = Profile.objects.get_or_create(user=user)
    if created and backend.name == 'google-oauth2':
        picture = response.get('picture')
        if picture:
            profile.profile_pic_url = picture
            profile.save()
