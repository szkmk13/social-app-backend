from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import re_path

from socialapp.bets.forms import BetCompletionForm
from socialapp.bets.models import Bet, Vote


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["user", "bet", "vote", "amount", "reward", "has_won"]
    list_filter = ["user", "has_won"]


class VoteInline(admin.TabularInline):
    model = Vote


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ["text", "label_1", "label_2", "ratio_1", "ratio_2", "deadline", "rewards_granted"]
    list_filter = ["rewards_granted"]
    actions = ["bet_completion"]
    ordering = [
        "rewards_granted",
        "deadline",
    ]
    inlines = [
        VoteInline,
    ]

    def calculate(self, request, queryset=None, *args, **kwargs):
        form = BetCompletionForm(request.POST)
        if not form.is_valid():
            self.message_user(request, "Choose correct", level=messages.ERROR)
            return HttpResponseRedirect("/admin/bets/bet")
        bet = Bet.objects.get(id=form.data["bet_id"])
        winning_answer = "a" if form.data.get("a") else "b"
        winning_ratio = bet.ratio_1 if winning_answer == "a" else bet.ratio_2

        winning_votes = bet.filter_votes_for(winning_answer)
        losing_votes = bet.exclude_votes_for(winning_answer)
        for vote in winning_votes:
            reward_for_user = vote.amount * winning_ratio

            vote.user.coins += reward_for_user
            vote.user.save(update_fields=["coins"])

            vote.has_won = True
            vote.reward = reward_for_user - vote.amount
            vote.save()
        losing_votes.update(has_won=False)
        bet.rewards_granted = True
        bet.save()
        self.message_user(request, "ok")
        return HttpResponseRedirect(request.build_absolute_uri().split("/calculate")[0])

    @admin.action(description="Close bet and payout")
    def bet_completion(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Select 1 bet", level=messages.ERROR)
            return
        bet = queryset.first()
        if bet.is_open:
            self.message_user(request, "Bet is still going, come back later", level=messages.ERROR)
            return
        if bet.rewards_granted:
            self.message_user(request, "Bet already paid", level=messages.ERROR)
            return

        form = BetCompletionForm()
        form.fields["a"].help_text = bet.label_1
        form.fields["b"].help_text = bet.label_2

        return render(
            request,
            "admin/bet_completion.html",
            context={
                "form": form,
                "path": "calculate/",
                "bet": bet,
            },
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [re_path("calculate/", self.calculate)]
        return custom_urls + urls
