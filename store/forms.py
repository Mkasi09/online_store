from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import ProductReview


class UsernameOrEmailAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                matching_users = list(User.objects.filter(email__iexact=username)[:2])
                if len(matching_users) == 1:
                    self.user_cache = authenticate(
                        self.request,
                        username=matching_users[0].get_username(),
                        password=password,
                    )

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'review-rating-input'}, choices=[
                (rating, f'{rating} star{"s" if rating != 1 else ""}')
                for rating in range(5, 0, -1)
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': 2000,
                'placeholder': 'Share your experience with this iPhone',
            }),
        }

    def clean_comment(self):
        comment = self.cleaned_data['comment'].strip()
        if len(comment) < 10:
            raise forms.ValidationError('Review comment must be at least 10 characters.')
        if len(comment) > 2000:
            raise forms.ValidationError('Review comment cannot exceed 2000 characters.')
        return comment
