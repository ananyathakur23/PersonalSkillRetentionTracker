from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Skill(models.Model):
    PRIORITY_CHOICES = [
        ('L', 'LOW'),
        ('M', 'MEDIUM'),
        ('H', 'HIGH'),
    ]

    CATEGORY_CHOICES = [
        ('TECH', 'Technical'),
        ('CREA', 'Creative'),
        ('SOFT', 'Soft Skills'),
        ('ACAD', 'Academic'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES)
    decay_rate = models.FloatField(default=2.0) #percent per day
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.priority == 'L':
            self.decay_rate = 1.0
        elif self.priority == 'M':
            self.decay_rate = 2.0
        elif self.priority == 'H':
            self.decay_rate = 3.5

        super().save(*args, **kwargs)
    
    @property
    def retention_score(self):
        #Calculate current retention score based on last practice
        last_log = self.practicelog_set.order_by('-date').first()
        
        if not last_log:
            # Never practiced — decay from creation date
            days_passed = (timezone.now().date() - self.created_at.date()).days
            score = 100 - (days_passed * self.decay_rate)
            return max(0, min(100, round(score, 2)))
        else:
            # Get days since last practice
            days_passed = (timezone.now().date() - last_log.date).days
            
            # Start from post-practice retention and decay
            score = last_log.post_practice_retention - (days_passed * self.decay_rate)
            final_score = max(0, min(100, round(score, 2)))
        
        from .models import UserStreak
        try:
            user_streak = UserStreak.objects.get(user=self.user)
            boost = user_streak.retention_boost
        except UserStreak.DoesNotExist:
            boost = 0

        final_score = max(0, min(100, final_score + boost))
        
        return final_score
        
    @property
    def days_since_last_practice(self):
        last_log = self.practicelog_set.order_by('-date').first()
        if not last_log:
            return (timezone.now().date() - self.created_at.date()).days
        return (timezone.now().date() - last_log.date).days
    
class PracticeLog(models.Model):
    QUALITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('DEEP', 'Deep'),
    ]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    quality = models.CharField(max_length=50, choices=QUALITY_CHOICES, default='MEDIUM')
    notes = models.TextField(blank=True, null=True)
    post_practice_retention = models.IntegerField(default=100, help_text="Retention % immediately after this practice")
    
    def save(self, *args, **kwargs):
        #Calculate post-practice retention based on previous practice and quality
        
        boost_map = {'LOW': 1, 'MEDIUM': 5, 'DEEP': 10}
        boost = boost_map.get(self.quality, 0)
        
        previous_log = PracticeLog.objects.filter(
            skill=self.skill,
            date__lt=self.date
        ).order_by('-date').first()
        
        if previous_log:
            # Calculate days between this practice and previous practice
            days_between = (self.date - previous_log.date).days
            
            # Decay from previous practice retention
            decayed_retention = previous_log.post_practice_retention - (days_between * self.skill.decay_rate)

            # Don't let decayed retention go below 0
            decayed_retention = max(0, decayed_retention)
            
        else:
            # No previous practice - start from creation date at 100%
            days_since_creation = (self.date - self.skill.created_at.date()).days
            decayed_retention = 100 - (days_since_creation * self.skill.decay_rate)
            decayed_retention = max(0, decayed_retention)
    
        new_retention = decayed_retention + boost
        self.post_practice_retention = max(0, min(100, round(new_retention, 2)))

        # Update user's streak when a new practice is logged
        from .models import UserStreak
        user_streak, created = UserStreak.objects.get_or_create(user=self.skill.user)
        user_streak.update_streak(self.date)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.skill.name} - {self.date}'

class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    last_streak_update = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        active = self.active_streak
        return f"{self.user.username} - {active} active days (best: {self.longest_streak})"
    
    def update_streak(self, practice_date):
        """Update streaks when user practices the skill"""
        today = timezone.now().date()
        
        # Only update for today
        if practice_date != today:
            return
        
        if self.last_activity_date == today:
            # Already practiced today, no change
            return
        
        if self.last_activity_date:
            days_gap = (today - self.last_activity_date).days
            if days_gap == 1:
                # Consecutive day
                self.current_streak += 1
            elif days_gap > 1:
                # Gap or first practice
                self.current_streak = 1
        else:
            # First ever practice
            self.current_streak = 1
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = today
        self.save()

    @property
    def active_streak(self):
        #Returns current active streak, resets if user missed a day
        if not self.last_activity_date:
            return 0
        
        today = timezone.now().date()
        days_since_last = (today - self.last_activity_date).days

        # If user missed a day, reset streak
        if days_since_last <= 1:
            return self.current_streak
        else:
            #Broken streak, reset to 0
            return 0
    
    @property
    def streak_level(self):
        """Return streak level for UI badges"""

        active = self.active_streak

        if active >= 30:
            return {'name': 'Master', 'icon': '🏆', 'color': 'gold'}
        elif active >= 14:
            return {'name': 'On Fire', 'icon': '🔥', 'color': 'orange'}
        elif active >= 7:
            return {'name': 'Consistent', 'icon': '⭐', 'color': 'blue'}
        elif active >= 3:
            return {'name': 'Building', 'icon': '🌱', 'color': 'green'}
        else:
            return {'name': 'Starting', 'icon': '📖', 'color': 'gray'}
    
    @property
    def retention_boost(self):
        """Retention boost percentage based on streak"""
        active = self.active_streak

        if active >= 30:
            return 15
        elif active >= 14:
            return 10
        elif active >= 7:
            return 5
        else:
            return 0
    
    def recalculate_streak(self):
        """Recalculate streak based on actual practice logs (call after deletion)"""
        from .models import PracticeLog
        
        # Get all distinct dates user practiced
        practice_dates = PracticeLog.objects.filter(
            skill__user=self.user
        ).dates('date', 'day', order='DESC')
        
        if not practice_dates:
            self.current_streak = 0
            self.last_activity_date = None
            self.save()
            return
        
        # Most recent practice date
        last_date = practice_dates[0]
        today = timezone.now().date()
        
        # If last practice was more than 1 day ago, streak is 0
        if (today - last_date).days > 1:
            self.current_streak = 0
            self.last_activity_date = last_date
            self.save()
            return
        
        # Count consecutive days backwards
        streak = 1
        expected = last_date - timezone.timedelta(days=1)
        
        for date in practice_dates[1:]:
            if date == expected:
                streak += 1
                expected -= timezone.timedelta(days=1)
            else:
                break
        
        self.current_streak = streak
        self.last_activity_date = last_date
        self.save()
    
@receiver(post_save, sender=User)
def create_user_streak(sender, instance, created, **kwargs):
    if created:
        UserStreak.objects.get_or_create(user=instance)

@receiver(models.signals.post_delete, sender=PracticeLog)
def recalculate_streak_on_delete(sender, instance, **kwargs):
    """When a practice log is deleted, recalculate the user's streak"""
    try:
        user_streak = UserStreak.objects.get(user=instance.skill.user)
        user_streak.recalculate_streak()
    except UserStreak.DoesNotExist:
        pass