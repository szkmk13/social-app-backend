from django import forms

from socialapp.utils import DetailException


class BetCompletionForm(forms.Form):
    a = forms.BooleanField(required=False)
    b = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        track = cleaned_data.get("a")
        session = cleaned_data.get("b")

        if track and session:
            self.add_error("a", DetailException("Choose 1"))
        if not track and not session:
            self.add_error("a", DetailException("Choose 1"))
        return cleaned_data
