# Generated by Django 4.2.13 on 2024-07-11 15:52

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bets', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bet',
            old_name='no_ratio',
            new_name='ratio_1',
        ),
        migrations.RenameField(
            model_name='bet',
            old_name='yes_ratio',
            new_name='ratio_2',
        ),
        migrations.RemoveField(
            model_name='bet',
            name='no_label',
        ),
        migrations.RemoveField(
            model_name='bet',
            name='open',
        ),
        migrations.RemoveField(
            model_name='bet',
            name='yes_label',
        ),
        migrations.RemoveField(
            model_name='vote',
            name='did_win',
        ),
        migrations.AddField(
            model_name='bet',
            name='label_1',
            field=models.CharField(default='TAK', max_length=50),
        ),
        migrations.AddField(
            model_name='bet',
            name='label_2',
            field=models.CharField(default='NIE', max_length=50),
        ),
        migrations.AddField(
            model_name='bet',
            name='rewards_granted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vote',
            name='has_won',
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='reward',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='bet',
            name='deadline',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bet',
            name='text',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='vote',
            name='amount',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='vote',
            name='bet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='bets.bet'),
        ),
        migrations.AlterField(
            model_name='vote',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='vote',
            name='vote',
            field=models.CharField(max_length=1),
        ),
    ]
